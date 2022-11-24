"""Вьюсеты для приложения API."""

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import IngredientSearchFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import AdminAuthorPermission
from .serializers import (CreateUpdateRecipeSerializer, FavoriteSerializer,
                          IngredientSerializer, ListRecipeSerializer,
                          ShoppingCartSerializer, SubscribeCreateSerializer,
                          SubscribeSerializer, TagSerializer)
from recipes.models import (Favorite, Ingredient, IngredientQuantity, Recipe,
                            ShoppingCart, Tag, User)
from users.models import Subscribe

User = get_user_model()


class UserViewSet(viewsets.GenericViewSet):
    """UserViewSet for API."""

    queryset = User.objects.all()
    pagination_class = CustomPagination
    serializer_class = SubscribeSerializer

    @action(
        detail=True,
        methods=('post',),
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk):
        """Эндпоинт подписки."""
        user = request.user
        author = get_object_or_404(User, id=pk)
        if user == author:
            return Response({
                'errors': 'Нельзя сотворить здесь!'
            }, status=status.HTTP_400_BAD_REQUEST)
        if Subscribe.objects.filter(following=user, author=author).exists():
            return Response({
                'errors': 'Нельзя подписыаться на одного автора дважды.'
            }, status=status.HTTP_400_BAD_REQUEST)
        subscribe = Subscribe.objects.create(following=user, author=author)
        serializer = SubscribeCreateSerializer(
            subscribe, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, pk):
        """Эндпоинт удаления подписки."""
        user = request.user
        author = get_object_or_404(User, id=pk)
        subscribe = get_object_or_404(
            Subscribe, following=user, author=author
        )
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        """
        Эндпоинт для выдачи авторов.

        Авторов, на которых существует подписка
        запрашивающего пользователя.
        """
        result = self.paginate_queryset(
            User.objects.filter(
                following__following=request.user
            )
        )
        serializer = SubscribeSerializer(
            result, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели ингредиентов API."""

    queryset = Ingredient.objects.all()
    pagination_class = None
    serializer_class = IngredientSerializer
    filterset_class = IngredientSearchFilter
    search_fields = ('^name',)


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Тегов API."""

    queryset = Tag.objects.all()
    pagination_class = None
    serializer_class = TagSerializer
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Рецептов API."""

    queryset = Recipe.objects.all()
    pagination_class = PageNumberPagination
    permission_classes = (IsAuthenticatedOrReadOnly, AdminAuthorPermission, )
    filterset_class = RecipeFilter
    search_fields = ('=name',)

    def get_serializer_class(self):
        """Метод для определения метода сериализации объекта."""
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return CreateUpdateRecipeSerializer
        return ListRecipeSerializer

    def perform_create(self, serializer):
        """Переопределение метода создания объекта."""
        return serializer.save(author=self.request.user)

    def recipe_post_method(self, request, AnySerializer, pk):
        """
        Метод для добавления объекта.

        Универсальный метод для добавления
        объектов связанных с рецептом.
        """
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        data = {
            'user': user.id,
            'recipe': recipe.id,
        }
        serializer = AnySerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def recipe_delete_method(self, request, AnyModel, pk):
        """
        Универсальный метод для удаления объекта.

        Объекта связанного с моделью рецепта.
        Избранное, список покупок.
        """
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        favorites = get_object_or_404(
            AnyModel, user=user, recipe=recipe
        )
        favorites.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['post', ],
        permission_classes=(IsAuthenticated, )
    )
    def favorite(self, request, pk=None):
        """Метод для добавления рецепта в список "избранное"."""
        return self.recipe_post_method(request, FavoriteSerializer, pk)

    @favorite.mapping.delete
    def delete_from_favorite(self, request, pk=None):
        """Метод для удаления рецепта из "избранного"."""
        return self.recipe_delete_method(request, Favorite, pk)

    @action(
        detail=True, methods=['post', ],
        permission_classes=(IsAuthenticated, )
    )
    def shopping_cart(self, request, pk=None):
        """Метод для добавления рецепта в список покупок."""
        return self.recipe_post_method(request, ShoppingCartSerializer, pk)

    @shopping_cart.mapping.delete
    def delete_from_shopping_card(self, request, pk=None):
        """Метод для удаления рецепта из списка покупок."""
        return self.recipe_delete_method(request, ShoppingCart, pk)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """
        Эндпоинт для скачивания списка ингредиентов.

        Для пользователя, сделавшего запрос,
        формируется список ингредиентов, собранный из
        всех рецептов добавленных пользователем в корзину.
        При совпадении ингредиентов в нескольких рецептах
        их количество суммируется.
        """
        shopping_cart = IngredientQuantity.objects.filter(
            current_recipe__cart_recipe__user=request.user
        ).values_list(
            'ingredient__name', 'ingredient__measurement_unit'
        ).order_by(
            'ingredient__name'
        ).annotate(
            ingredient_total=Sum('amount')
        )
        text = 'Cписок покупок: \n'
        for ingredients in shopping_cart:
            name, measurement_unit, amount = ingredients
            text += f'{name}: {amount} {measurement_unit}\n'
        response = HttpResponse(text, content_type='text/plain')
        filename = 'shop-list.pdf'
        response['Content-Disposition'] = (
            f'attachment; filename={filename}'
        )
        return response
