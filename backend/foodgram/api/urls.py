"""URL's for API."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (UserViewSet, IngredientViewSet, RecipeViewSet,
                    TagViewSet)

v1_router = DefaultRouter()
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')
v1_router.register('tags', TagViewSet, basename='tags')
v1_router.register('recipes', RecipeViewSet, basename='recipes')
v1_router.register('users', UserViewSet, basename='users')
app_name = 'api'
urlpatterns = [
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(v1_router.urls)),
]
