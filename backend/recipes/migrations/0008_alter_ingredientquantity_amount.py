# Generated by Django 3.2.16 on 2022-11-25 10:34

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0007_auto_20221124_1428'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientquantity',
            name='amount',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1, message='Количество не может быть меньше 1!')], verbose_name='Количество ингредиента'),
        ),
    ]
