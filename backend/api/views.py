"""Вьюсеты для приложения API."""

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .permissions import AdminAuthorPermission, AdminOrReadOnlyPermission
from .serializers import (CreateUpdateRecipeSerializer, FavoriteSerializer,
                          IngredientSerializer, ListRecipeSerializer,
                          ShoppingCartSerializer, SubscribeCreateSerializer,
                          SubscribeSerializer, TagSerializer, UserSerializer)
from recipes.models import (Favorite, Ingredient, IngredientQuantity, Recipe,
                            ShoppingCart, Tag, User)
from users.models import Subscribe

User = get_user_model()


class UserViewSet(viewsets.GenericViewSet):
    """UserViewSet for API."""

    queryset = User.objects.all()
    pagination_class = PageNumberPagination
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """
        Эндпоинт для выдачи авторов.

        Авторов, на которых существует подписка
        запрашивающего пользователя.
        """

        result = self.paginate_queryset(request.user.subscriber.all())
        serializer = SubscribeSerializer(
            result, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Эндпоинт подписки."""
        user = request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            return Response({
                'errors': 'Нельзя сотворить здесь!'
            }, status=status.HTTP_400_BAD_REQUEST)
        if Subscribe.objects.filter(user=user, author=author).exists():
            return Response({
                'errors': 'Нельзя подписыаться на одного автора дважды.'
            }, status=status.HTTP_400_BAD_REQUEST)
        subscribe = Subscribe.objects.create(user=user, author=author)
        serializer = SubscribeCreateSerializer(
            subscribe, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        """Эндпоинт удаления подписки."""
        user = request.user
        author = get_object_or_404(User, id=id)
        subscribe = get_object_or_404(
            Subscribe, user=user, author=author
        )
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели ингредиентов API."""

    queryset = Ingredient.objects.all()
    pagination_class = None
    serializer_class = IngredientSerializer
    permission_classes = (AdminOrReadOnlyPermission, )
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, )
    filterset_fields = ('name', )
    search_fields = ('=name',)
    lookup_field = 'pk'


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Тегов API."""

    queryset = Tag.objects.all()
    pagination_class = None
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnlyPermission, )
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, )
    filterset_fields = ('name', )
    search_fields = ('=name',)
    lookup_field = 'name'


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Рецептов API."""

    queryset = Recipe.objects.all()
    pagination_class = PageNumberPagination
    permission_classes = (AdminAuthorPermission, )
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, )
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
        queryset = self.get_queryset()
        cart_objects = ShoppingCart.objects.filter(user=request.user)
        recipes = queryset.filter(shoppingcart__in=cart_objects)
        ingredients = IngredientQuantity.objects.filter(recipes__in=recipes)
        ingredients_list = Ingredient.objects.filter(
            quantity__in=ingredients
        ).annotate(total=Sum('quantity__quantity'))

        fields = [f'{ingredient.name}, {ingredient.total}'
                  f' {ingredient.measurement_unit}'
                  for ingredient in ingredients_list]
        filename = 'ingredients.txt'
        response_content = '\n'.join(fields)
        response = HttpResponse(response_content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
