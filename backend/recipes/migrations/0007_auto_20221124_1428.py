# Generated by Django 3.2.16 on 2022-11-24 08:28

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0006_auto_20221123_1900'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveSmallIntegerField(help_text=('Укажите примерное время,необходимое для приготовления Вашего блюда.',), validators=[django.core.validators.MinValueValidator(1, message='Время приготовления не может быть меньше 1 мин.')], verbose_name='Время приготовления'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='image',
            field=models.ImageField(default=1, upload_to='recipes/media/', verbose_name='Картинка'),
            preserve_default=False,
        ),
    ]
