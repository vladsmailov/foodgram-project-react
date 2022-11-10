"""Модели для приложения recipes."""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.html import format_html

User = get_user_model()
MEASUREMENT_UNIT_CHOICES = (
    ("1", "мг"),
    ("2", "г"),
    ("3", "кг"),
    ("4", "мл"),
    ("5", "л"),
    ("6", "шт"),
)


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        max_length=1000,
        verbose_name='Название ингредиента',
        help_text=(
            f'{"Напишите понятное название ингредиента."}'
        )
    )
    measurement_unit = models.CharField(
        max_length=20,
        choices=MEASUREMENT_UNIT_CHOICES,
        default='г'
        )

    class Meta:
        """Meta for Ingredients."""

        ordering = ('name', )

    def __str__(self):
        """Метод вывода в строковый формат ингредиента."""
        return self.name


class IngredientQuantity(models.Model):
    """Модель для ингредиента и указания его количества."""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='quantity'
    )
    quantity = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента',
        default=0
    )

    def __str__(self):
        """
        Метод вывода в строковый формат.

        Ингредиента и его количества.
        """
        return f'{self.quantity} {self.ingredient}'


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        max_length=100,
        verbose_name='Тег рецепта',
        help_text=(
            f'{"Категория к которой Вы бы отнесли свой рецепт."}'
            f'{"Одним словом."}'
        )
    )
    slug = models.SlugField(
        verbose_name='Уникальное название тега',
        help_text='Добавьте уникальный ID для тега',
        unique=True
    )
    color = models.CharField(max_length=7, default="#ffffff")

    def colored_name(self):
        """Метод для вывода цвета в формате #######."""
        return format_html(
            '<span style="color: #{};">{}</span>',
            self.color,
        )

    class Meta:
        """Мета для объектов Тег."""

        ordering = ('name', )

    def __str__(self):
        """Метод вывода в строковый формат тега."""
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        verbose_name=('Автор рецепта'),
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Название рецепта',
        help_text=(
            f'{"Придумайте название рецепта,"}'
            f'{"отражающее его суть или просто интересное название :)"}'
        )
    )
    image = models.ImageField(
        "Картинка",
        upload_to="recipes/",
        blank=True,
        null=True
    )
    cooking_time = models.TimeField(
        verbose_name='Время приготовления',
        help_text=(
            f'{"Укажите примерное время,"}'
            f'{"необходимое для приготовления Вашего блюда."}',
        )
    )
    text = models.TextField(
        'Описание рецепта',
        help_text=(
            f'{"Напишите рецепт блюда,"}'
            f'{"чтобы его смог приготовить любой желающий!"}'
        )
    )
    ingredients = models.ManyToManyField(
        IngredientQuantity,
        related_name='recipes',
        verbose_name='Ингредиенты',
        help_text='Выберите ингредиенты для рецепта'
        )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
        help_text='Выберите теги для рецепта'
        )
    is_favorited = models.BooleanField(
        'В списке избранных', default=False
    )
    is_in_shopping_cart = models.BooleanField(
        'В списке покупок',
        default=False
    )

    class Meta:
        """Мета для рецепта."""

        ordering = ('name', )

    def __str__(self):
        """Метод вывода в строковый формат рецепта."""
        return self.name


class Favorite(models.Model):
    """Модель объекта рецепта добавленного в избранное."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipe_subscriber',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe'
    )

    class Meta:
        """Мета для модели добавления в избранное."""

        verbose_name = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='favorite_user_recept_unique'
            )
        ]

    def __str__(self):
        """Метод вывода в строковый формат списка "избранное"."""
        return f'Рецепт {self.recipe} в избранном у {self.user}'


class Subscribe(models.Model):
    """Модель подписки на автора рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribed_to',
    )

    def __str__(self):
        """Метод вывода в строковый формат объектов подписки."""
        return f'{self.user} подписан на {self.author}'


class ShoppingCart(models.Model):
    """Модель списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_card_owner',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shoppingcart'
    )

    class Meta:
        """Мета для модели добавления в избранное."""

        verbose_name = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='Shopping_cart_recept_unique'
            )
        ]

    def __str__(self):
        """Метод вывода в строковый формат списка покупок."""
        return f'Рецепт {self.recipe} в списке у {self.user}'
