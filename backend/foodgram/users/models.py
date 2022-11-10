"""Меодель приложения users."""
from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, EmailField, ManyToManyField


class CustomUser(AbstractUser):
    """Модель пользователя."""

    username = CharField(
        verbose_name='Уникальный username',
        max_length=150,
        unique=True,
        help_text='Укажите username от 3 до 150 букв',
    )
    email = EmailField(
        verbose_name='Адрес электронной почты',
        max_length=254,
        unique=True,
        help_text='Введите адрес электронной почты'
    )
    first_name = CharField(
        verbose_name='Имя',
        max_length=150
    )
    last_name = CharField(
        verbose_name='Фамилия',
        max_length=150
    )
    password = CharField(
        verbose_name='password',
        max_length=150
    )
    is_subscribed = ManyToManyField(
        verbose_name='Подписка',
        related_name='subscribers',
        to='self',
        symmetrical=False,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        """Мета для модели пользователя."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        """Метод вывода в строковом формате."""
        return f'{self.username}: {self.email}'
