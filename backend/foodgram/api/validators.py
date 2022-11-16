"""Валидаторы для приложения api."""
from django.core.exceptions import ValidationError

def ingredients_validator(value):
    if len(set(value)) != len(value):
        raise ValidationError('Нельзя добавить один и тот же ингредиент дважды.')