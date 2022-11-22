Данные для тестирования ревьюером:
email == vladsmailov@gmail.com
password == 355-ad5-Uem-Eje


# Vladsmailov yandex-praktikum diplom project.
## Проект foodgram (продуктовый ассистент).
# Создан с применением стека технологий:

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)
![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white)

# Vlad_Smailov_foodgram

[![foodgram-app workflow](https://github.com/vladsmailov/foodgram-project-react/actions/workflows/foodgram-workflow.yml/badge.svg)](https://github.com/vladsmailov/foodgram-project-react/actions/workflows/foodgram-workflow.yml)

# Описание проекта

>Ссылка на сайт [foodgram](http://51.250.98.163/)

> Продуктовый ассистент - это помощник для приготоления блюд, здесь вы можете размещать свои рецепты, а так же делиться своими собственными, подписываться на авторов и добавлять рецепты в избранное и продуктовую корзину, которую потом можно будет распечатать и взять с собой в магазин!
## Как запустить проект:
**Клонировать репозиторий и перейти в него в командной строке:**

> git@github.com:vladsmailov/foodgram-project-react.git

```
cd foodgram-project-react
```

**Cоздать и активировать виртуальное окружение:**

```
python -m venv env
venv/scripts/activate.ps1
```

**Установить зависимости из файла requirements.txt:**

```
cd .\backend\
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Предварительно установим Docker на ПК:**

> https://www.docker.com/products/docker-desktop/

***ВАЖНО! Для корректной работы Docker на ПК с ОС WINDOWS нужно настроить систему виртуализации. Для разных версий Windows доступны разные системы виртуализации.***

**Рассмотрим установку Docker на ОС Linux.**

```
sudo apt update && apt upgrade -y
```

**Удаляем старый Docker:**
```
sudo apt remove docker
```

**Устанавливаем Docker:**

```
sudo apt install docker.io
```

**Запускаем Docker:**

```
sudo systemctl start docker
```

**Откроем образ hello-world для проверки:**

```
docker run hello-world 
```

**Создадим в папке infra файл с переменными окружения .env:**

```
cd infra
nano .env
```
```
DB_ENGINE=django.db.backends.postgresql 
DB_NAME=postgres 
POSTGRES_USER=postgres 
POSTGRES_PASSWORD=postgres 
DB_HOST=db 
DB_PORT=5432
```

**В settings.py добавляем следующее:**

```
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', default='postgres'),
        'USER': os.getenv('POSTGRES_USER', default='postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', default='my_key_for_test'),
        'HOST': os.getenv('DB_HOST', default='db'),
        'PORT': os.getenv('DB_PORT', default='5432')
    }
}
```

**Перейдем в директорию infra и создадим контейнеры:**
```
sudo docker compose up -d --build
```

**В контейнере backend выполним миграции, создадим админа и соберем статику в одну папку:**
```
sudo docker compose exec backend python manage.py migrate
sudo docker compose exec backend python manage.py createsuperuser
sudo docker compose exec backend python manage.py collectstatic --no-input
```

**Все готово, добавляем тестовые данные и можно работать!**
**Тестовые адреса для проверки:**

>http://localhost/ - главная страница сайта;

>http://localhost/admin/ - админ панель;

>http://localhost/api/ - API проекта

>http://localhost/api/docs/redoc.html - документация к API

## Автор проекта: [Смаилов Владислав](https://github.com/vladsmailov).