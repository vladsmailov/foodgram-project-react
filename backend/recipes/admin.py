"""Файл админки для приложения recipes."""

from django.contrib import admin
from django.utils.html import format_html

from .models import (Favorite, Ingredient, IngredientQuantity, Recipe,
                     ShoppingCart, Tag)


class BaseAdminSettings(admin.ModelAdmin):
    """Настройки панели администартора."""

    empty_value_display = '-пусто-'
    list_filter = ('author', 'name', 'tags')


class IngredientAdmin(BaseAdminSettings):
    """Настройка панели ингредиентов."""

    list_display = (
        'name',
        'measurement_unit'
    )
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class IngredientQuantityInLine(admin.TabularInline):
    """
    Настройки админ зоны
    модели ингредиентов в рецепте.
    """

    model = IngredientQuantity
    extra = 0
    min_num = 1


class TagAdmin(BaseAdminSettings):
    """Настройка панели тегов."""

    list_display = (
        'name',
        'colored',
        'slug'
    )
    list_display_links = ('name', 'colored', 'slug',)
    search_fields = ('name', 'slug')
    list_filter = ('name',)
    empty_value_display = '-пусто-'

    @admin.display
    def colored(self, obj):
        return format_html(
            f'<span style="background: {obj.color};'
            f'color: {obj.color}";>___________</span>'
        )
    colored.short_description = 'цвет'


class RecipeAdmin(BaseAdminSettings):
    """Настройка панели рецептов."""

    list_display = (
        'name', 'author', 'text',
        'cooking_time', 'id', 'image',
    )
    list_display_links = ('name',)
    search_fields = ('name', 'author', 'tags')
    list_filter = ('author', 'name', 'tags')
    filter_horizontal = ('tags',)
    inlines = (IngredientQuantityInLine,)
    exclude = ('ingredients', )
    empty_value_display = '-пусто-'


class FavoriteAdmin(admin.ModelAdmin):
    """Настройка панели избранное."""

    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user', 'recipe')


class ShoppingCartAdmin(admin.ModelAdmin):
    """Настройка панели корзины."""

    list_display = ('recipe', 'user')
    list_filter = ('recipe', 'user')
    search_fields = ('user',)


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
