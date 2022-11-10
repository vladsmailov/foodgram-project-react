"""
Сериализаторы/Десериализаторы для приложения api.

Данный раздел отвечает за преобразование данных,
такие как наборы запросов и экземпляры моделей,
в собственные типы данных Python. А так же
преобразовывать разобранные данные обратно в сложные типы.
"""
import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, IngredientQuantity, Recipe,
                            ShoppingCart, Subscribe, Tag, User)


class Base64ImageField(serializers.ImageField):
    """
    Сериализатор Base64ImageField.

    Служит для перобразования изображения из закодированного текстового формата
    в изображение, которое сохранится в папке на сервере.
    """

    def to_internal_value(self, data):
        """Функция для декодирования изображения."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')

        return super().to_internal_value(data)


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
            'is_subscribed',
        )
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = 'is_subscribed',

    def get_is_subscribed(self, obj):
        """Проверка подписки пользователя."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscribe.objects.filter(
            user=request.user,
            author=obj.id).exists()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов для приложения api."""

    class Meta:
        """Мета для сериализатора тегов."""

        model = Tag
        fields = ('name',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингердиентов для приложения API."""

    class Meta:
        """Мета для сериализатора ингредиентов."""

        model = Ingredient
        fields = '__all__'


class IngredientQuantitySerialized(serializers.ModelSerializer):
    """Сериализатор для определения количества ингредиентов."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.SerializerMethodField(read_only=True)
    measurement_unit = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Мета для сериализатора связывающего ингредиент и его количество."""

        model = IngredientQuantity
        fields = ('id', 'name', 'measurement_unit', 'quantity')

    def _get_ingredient(self, ingredient_id):
        """Метод отвечающий за выдачу нужного ингредиента."""
        return get_object_or_404(Ingredient, id=ingredient_id)

    def get_name(self, quantity):
        """Метод отвечающий за выдачу нужного имени ингредиента."""
        return self._get_ingredient(quantity.ingredient.id).name

    def get_measurement_unit(self, quantity):
        """Метод отвечающий за выдачу нужной единицы измерения."""
        return self._get_ingredient(quantity.ingredient.id).measurement_unit


class ListRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для вывода данных при запросе к эндпоинту recipes.

    При GET-запросе выводит данные в формате json.
    """

    image = Base64ImageField(required=False, allow_null=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientQuantitySerialized(many=True)
    tags = TagSerializer(many=True)
    is_in_favorite = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        """Мета для сериализатора рецептов."""

        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'image',
            'name', 'text', 'cooking_time', 'is_in_favorite',
            'is_in_shopping_cart',
            )

    def get_is_in_favorite(self, obj):
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

    image = Base64ImageField(required=False, allow_null=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientQuantitySerialized(many=True)
    tags = TagSerializer(many=True)

    class Meta:
        """Мета для десериализатора рецептов."""

        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'image',
            'name', 'text', 'cooking_time', 'is_favorited',
            'is_in_shopping_cart'
            )

    def create(self, validated_data):
        """Метод для создания новых записей рецептов в БД."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        image = validated_data.pop('image')
        recipe = Recipe.objects.create(image=image, **validated_data)
        ingredients_list = []
        tags_list = []
        for ingredient in ingredients:
            current_ingredient, _ = IngredientQuantity.objects.get_or_create(
                **ingredient)
            ingredients_list.append(current_ingredient)
        for tag in tags:
            current_tag, _ = Tag.objects.get_or_create(
                **tag)
            tags_list.append(current_tag)
        recipe.ingredients.set(ingredients_list)
        recipe.tags.set(tags_list)
        return recipe

    def update(self, instance, validated_data):
        """Метод для обновления уже существующих рецептов в БД."""
        self.name = validated_data.get('name', instance.name)
        self.image = validated_data.get('image', instance.image)
        self.text = validated_data.get('text', instance.text)
        self.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
            )

        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            ingredients_list = []
            for ingredient in ingredients:
                current_ingredient = (
                    IngredientQuantity.objects.get_or_create(**ingredient)
                    )
                ingredients_list.append(current_ingredient)
            instance.ingredients.set(ingredients_list)
        instance.save()
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецептов в избранное."""

    name = serializers.ReadOnlyField(source='recipe.name')
    id = serializers.ReadOnlyField(source='recipe.id')

    class Meta:
        """Мета для сериализатора добавления рецептов в избранное."""

        model = Favorite
        fields = ('name', 'id', 'user', 'recipe',)

    def validate(self, data):
        """Метод для валидации данных сериализатора "избранное"."""
        if Favorite.objects.filter(user=data['user'],
                                   recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже в списке избранных.'
            )
        return data


class RecipeSubscribedToSerializer(serializers.ModelSerializer):
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

    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipe_count = serializers.SerializerMethodField()

    class Meta:
        """Мета для сериализатора подписки."""

        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipe_count')

    def get_is_subscribed(self, object):
        """Поле-индикатор наличия подписки на автора."""
        return Subscribe.objects.filter(
            user=object.user, author=object.author
        ).exists()

    def get_recipes(self, object):
        """Метод для выдачи рецептов определенного автора."""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=object.author)
        if limit:
            queryset = queryset[:int(limit)]
        return RecipeSubscribedToSerializer(queryset, many=True).data

    def get_recipe_count(self, object):
        """Количество рецептов автора."""
        return Recipe.objects.filter(author=object.author).count()


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
        return RecipeSubscribedToSerializer(
            instance.recipe,
            context=context).data
