"""Меодель приложения users."""
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """Модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    username = models.CharField(
        validators=(
            RegexValidator(regex=r'^[\w.@+-]+$',),
            RegexValidator(
                regex=r'^\b(m|M)(e|E)\b',
                inverse_match=True,
                message="""Недопустимое имя пользователя."""
            ),
        ),
        verbose_name='Уникальный username',
        max_length=150,
        unique=True,
        help_text='Укажите username от 3 до 150 букв',
    )
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=254,
        unique=True,
        help_text='Введите адрес электронной почты'
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150
    )
    password = models.CharField(
        verbose_name='password',
        max_length=150
    )

    class Meta:
        """Мета для модели пользователя."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        """Метод вывода в строковом формате."""
        return f'{self.username}: {self.email}'


class Subscribe(models.Model):
    """Модель подписки на автора рецептов."""

    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        """Мета модели подписки."""
        constraints = [
            models.UniqueConstraint(fields=["author", "following"],
                                    name="user_following"),
            models.CheckConstraint(
                check=~models.Q(author=models.F('following')),
                name='not_self_following_author'
            )
        ]

    def __str__(self):
        """Метод вывода в строковый формат объектов подписки."""
        return f'{self.following} подписан на {self.author}'
