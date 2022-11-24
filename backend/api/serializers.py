"""
Сериализаторы/Десериализаторы для приложения api.

Данный раздел отвечает за преобразование данных,
такие как наборы запросов и экземпляры моделей,
в собственные типы данных Python. А так же
преобразовывать разобранные данные обратно в сложные типы.
"""

from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from recipes.models import (Favorite, Ingredient, IngredientQuantity, Recipe,
                            ShoppingCart, Tag, User)
from users.models import Subscribe


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Мета для сериализатора пользователя."""

        model = User
        fields = (
            'email',
            'id',
            'first_name',
            'last_name',
            'username',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj: User):
        """Метод вывода данных о подписке."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscribe.objects.filter(
            following=request.user, author=obj).exists()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов для приложения api."""

    class Meta:
        """Мета для сериализатора тегов."""

        model = Tag
        fields = '__all__'


class TagListSerializer(serializers.RelatedField):
    """ Сериализатор для получения списка тегов"""

    def to_representation(self, obj):
        """Метод вывода результатов."""
        return {
            'id': obj.id,
            'name': obj.name,
            'color': obj.color,
            'slug': obj.slug
        }

    def to_internal_value(self, data):
        """Метод валдиации и обновления данных запроса."""
        try:
            return Tag.objects.get(id=data)
        except ObjectDoesNotExist as e:
            raise serializers.ValidationError(
                'Недопустимый первичный ключ "404" - объект не существует.'
            ) from e


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингердиентов для приложения API."""

    class Meta:
        """Мета для сериализатора ингредиентов."""

        model = Ingredient
        fields = '__all__'


class IngredientQuantitySerializer(serializers.ModelSerializer):
    """Сериализатор для определения количества ингредиентов."""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all(),
    )

    class Meta:
        model = IngredientQuantity
        fields = (
            'id',
            'amount',
        )

    def validate_quantity(self, data):
        """Метод валидации данных."""
        if int(data) < 1:
            raise ValidationError({
                'ingredients': (
                    'Количество должно быть больше 1'
                ),
                'msg': data
            })
        return data

    def create(self, validated_data):
        return IngredientQuantity.objects.create(
            ingredient=validated_data.get('id'),
            amount=validated_data.get('amount')
        )


class IngredientQuantityShowSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода данных об снгредиентах в рецептах."""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        read_only=True
    )
    measurement_unit = serializers.SlugRelatedField(
        source='ingredient',
        slug_field='measurement_unit',
        read_only=True,
    )
    name = serializers.SlugRelatedField(
        source='ingredient',
        slug_field='name',
        read_only=True,
    )

    class Meta:
        """Мета для сериализатора Ингредиенты-количество-Рецепты."""
        model = IngredientQuantity
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class ListRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для вывода данных при запросе к эндпоинту recipes.

    При GET-запросе выводит данные в формате json.
    """

    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField(
        read_only=True
    )
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        """Мета для сериализатора рецептов."""

        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'image',
            'name', 'text', 'cooking_time', 'is_favorited',
            'is_in_shopping_cart',
        )

    @staticmethod
    def get_ingredients(obj):
        """Метод получения ингредиента для вывода данных."""
        ingredients = IngredientQuantity.objects.filter(current_recipe=obj)
        return IngredientQuantityShowSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        """Метод для отображения наличия рецепта в "избранном"."""
        request = self.context.get('request')
        if request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user,
                                           recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """
        Метод для выдачи нужного флага.

        Фактически метод выполняющй функцию permission и
        присвоения нужному полю объекта recipe нужного флага.
        True или False. Отвечает за выдачу информации о том
        добавлен ли рецепт в список покупок.
        """
        request = self.context.get('request')
        if request.user.is_authenticated:
            return ShoppingCart.objects.filter(user=request.user,
                                               recipe=obj).exists()
        return False


class CreateUpdateRecipeSerializer(serializers.ModelSerializer):
    """Десериализатор для создания новых рецептов и обновления старых."""

    image = Base64ImageField(use_url=True, max_length=None)
    author = UserSerializer(read_only=True)
    ingredients = IngredientQuantitySerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta:
        """Мета для десериализатора рецептов."""

        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'image',
            'name', 'text', 'cooking_time',
        )

    @atomic
    def create(self, validated_data):
        """Метод для создания новых записей рецептов в БД."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    def create_ingredients(self, recipe, ingredients):
        """Метод для создания списка ингредиентов."""
        IngredientQuantity.objects.bulk_create([
            IngredientQuantity(
                current_recipe=recipe,
                amount=ingredient['amount'],
                ingredient=ingredient['ingredient'],
            ) for ingredient in ingredients
        ])

    def validate(self, data):
        """Валидация полей рецепта перед созданием экзмепляра."""
        ingredients = self.initial_data.get('ingredients')
        ingredients_list = []
        for ingredient in ingredients:
            if ingredient['id'] in ingredients_list:
                raise ValidationError(
                    'Нельзя добавлять один и тот же ингредиент дважды.'
                )
            ingredients_list.append(ingredient['id'])
        if data['cooking_time'] <= 0:
            raise ValidationError(
                'Увы, но мгновенное приготовление блюда невозможно.'
            )
        return data

    @atomic
    def update(self, instance, validated_data):
        """Метод для обновления уже существующих рецептов в БД."""
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        if 'ingredients' in validated_data:
            recipe = instance
            ingredients = validated_data.pop('ingredients')
            IngredientQuantity.objects.filter(current_recipe=recipe).delete()
            self.create_ingredients(recipe, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        """Метод вывода данных созданного объекта."""
        return ListRecipeSerializer(
            instance,
            context={
                'request': self.context.get('request'),
            }
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецептов в избранное."""

    name = serializers.ReadOnlyField(source='recipe.name')
    id = serializers.ReadOnlyField(source='recipe.id')

    class Meta:
        """Мета для сериализатора добавления рецептов в избранное."""

        model = Favorite
        fields = ('name', 'id', 'user', 'recipe',)

    def to_representation(self, instance):
        """Метод отображения данных."""
        request = self.context.get('request')
        context = {'request': request}
        return RecipeShortShowSerializer(
            instance.recipe, context=context).data


class RecipeShortShowSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения нужных полей объекта рецепты.

    Для автора на которого есть подписка.
    """

    class Meta:
        """Мета для сериализатора объектов рецептов с подпиской."""

        model = Recipe
        fields = ('name', 'id', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения авторов НА которых существует подписка."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        """Мета для сериализатора подписки."""

        model = User
        fields = UserSerializer.Meta.fields + (
            'recipes', 'recipes_count', 'is_subscribed'
        )

    def get_is_subscribed(self, obj: User):
        """Метод вывода данных о подписке."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscribe.objects.filter(
            following=request.user, author=obj).exists()

    def get_recipes(self, author):
        """Метод получения рецепта."""
        queryset = self.context.get('request')
        recipes_limit = queryset.query_params.get('recipes_limit')
        if not recipes_limit:
            return RecipeShortShowSerializer(
                Recipe.objects.filter(author=author),
                many=True, context={'request': queryset}
            ).data
        return RecipeShortShowSerializer(
            Recipe.objects.filter(author=author)[recipes_limit],
            many=True,
            context={'request': queryset}
        ).data

    def get_recipes_count(self, author):
        """Количество рецептов автора."""
        return author.recipes.all().count()


class SubscribeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления объекта подписки."""

    class Meta:
        """Мета для сериализатора создания подписки."""
        model = Subscribe
        fields = ('following', 'author')

    def validate(self, data):
        """Метод валидации данных."""
        get_object_or_404(User, username=data['author'])
        if self.context['request'].following == data['author']:
            raise ValidationError({
                'errors': 'Нельзя подписаться на самого себя.'
            })
        if Subscribe.objects.filter(
                following=self.context['request'].following,
                author=data['author']
        ):
            raise ValidationError({
                'errors': 'Уже подписан.'
            })
        return data

    def to_representation(self, instance):
        """Метод вывода данных."""
        return SubscribeSerializer(
            instance.author,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления/удаления рецептов из списка покупок."""

    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ReadOnlyField(source='recipe.image')
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        """Мета для сериализатора добавления рецептов в список покупок."""

        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time', 'user', 'recipe')

    def validate(self, data):
        """
        Валидация данных при обработке запроса.

        Проверяем, присутствует ли данный рецепт в списке покупок.
        """
        if ShoppingCart.objects.filter(
            user=data['user'],
            recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                'Рецепт уже в списке покупок.'
            )
        return data

    def to_representation(self, instance):
        """Метод для вывода данных при GET-запросе."""
        request = self.context.get('request')
        context = {'request': request}
        return RecipeShortShowSerializer(
            instance.recipe,
            context=context).data
