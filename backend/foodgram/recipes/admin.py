"""Файл админки для приложения recipes."""

from django.utils.html import format_html

from django.contrib import admin
from .models import (
    Ingredient, IngredientQuantity, Tag, 
    Recipe, Favorite, ShoppingCart
)

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



class IngredientQuantityAdmin(admin.ModelAdmin):
    """
    Настройка панели ингредиенты-рецепты-количество.
    """
    list_display = (
        'current_recipe',
        'ingredient',
        'quantity',
    )
    list_filter = ('recipe', 'ingredient')


class IngredientQuantityInLine(admin.TabularInline):
    """
    Настройки админ зоны
    модели ингредиентов в рецепте.
    """

    model = IngredientQuantity
    extra = 0


class TagAdmin(BaseAdminSettings):
    """Настройка панели тегов."""

    list_display = (
        'name',
        'color',
        'slug'
    )
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)

    def colored_name(self):
        """Метод для вывода цвета в формате #######."""
        return format_html(
            '<span style="color: #{};">{}</span>',
            self.color,
        )


class RecipeAdmin(BaseAdminSettings):
    """Настройка панели рецептов."""

    list_display = (
        'name',
        'author',
        'is_favorite'
    )
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('author', 'name', 'tags')
    readonly_fields = ('is_favorite',)
    filter_horizontal = ('tags',)
    inlines = (IngredientQuantityInLine,)

    def is_favorite(self, obj):
        return obj.is_favorite.all().count()


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
admin.site.register(IngredientQuantity, IngredientQuantityAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
