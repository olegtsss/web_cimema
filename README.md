# Описание проекта web_cinema:
Backend онлайн кинотеатра: админка, полнотекстовый поиск, сервисы авторизации, UGC контента, нотификации и биллинга.

### Используемые технологии:

Python, Django, FastAPI, Flask, OAuth, JWT, ElasticSearch, Redis, Kafka, RabbitMQ, ELK, Docker-compose

### Архитектура проекта:
- `admin/movies_admin` - панель администратора, позволяет создавать и редактировать записи в базе данных: интерфейс панели администратора настроен стандартными средствами Django, в нём можно создавать, редактировать и удалять кинопроизведения, жанры и персон, связи между кинопроизведениями, жанрами и персонами заводятся на странице редактирования кинопроизведения, все тексты переведены на русский с помощью `gettext_lazy`. Возможности API: `/api/v1/movies/` (GET): получить информацию о всех кинопроизведениях из базы данных; `/api/v1/movies/{uuid_id}` (GET): получить информацию о конкретном кинопроизведении.
- `admin/etl` - отказоустойчивый перенос данных из Postgres в Elasticsearch, настроена поисковая система.
- `api` - реализация API для кинотеатра на базе `Fastapi`. Позволяет выполнять запрос фильма, жанра, персоны по id, поиск по keyword (title) в фильме, поиск по персоне, список всех фильмов, всех жанров, фильмов по персоне, сортировка по полям, фильтр по жанрам в фильмах.
- `auth` - сервис работы с пользователями на базе `Fastapi`. Позволяет выполнять регистрацию пользователей, вход пользователя в аккаунт (обмен логина и пароля на пару токенов: JWT-access токен и refresh токен), обновление access-токена, выход пользователя из аккаунта, изменение логина или пароля, получение пользователем своей истории входов в аккаунт, CRUD для управления ролями. Oauth реализован для `vk` и `yandex`.
- `ugc` - сервис сбора пользовательских действий на базе `Flask`. Может отслеживать клики, просмотры страниц, а также кастомные события (смена качества видео, просмотр видео до конца, использование фильтров поиска). В качестве хранилищ задействованы nosql субд `MongoDB` (в качестве data lake) и колоночная субд `ClickHouse` для хранения событий.
- `notif` - сервис отправки уведомлений на базе `Fastapi`. Включает api для приёма событий по созданию уведомлений, загрузки их в брокер событий, обработке их и обогащению (посредством взаимодействия с сервисом `auth`), загрузки в очередь доставки, рассылки уведомлений (email и websockets).
- `billing` - cервис позволяет работать c подписками для кинотеатра: оплатить подписку и вернуть за неё деньги. Реализованы сценарии принятия платежей по картам от пользователей и возврата средств по ранее сделанным платежам. Выполнена интеграция с платежными шлюзами `ЯПей` (https://console.pay.yandex.ru/) и `ЮКасса` (https://yookassa.ru/).

### Запуск биллинг сервиса:

```bash
cd src/
alembic upgrade head
python3 -m gunicorn main:app -c gunicorn.conf.py
```

* Добавление ежедневных проверок в планировщик:

```bash
crontab -e

0 0 * * * /path/to/project/venv/bin/python /path/to/project/src/cli.py check_new_free_orders
0 0 * * * /path/to/project/venv/bin/python /path/to/project/src/cli.py check_new_orders
0 0 * * * /path/to/project/venv/bin/python /path/to/project/src/cli.py check_active_recurent_orders
0 0 * * * /path/to/project/venv/bin/python /path/to/project/src/cli.py check_expired_orders
```

* Docker:

```bash
docker-compose exec billing sh
apt-get update && apt-get install -y cron nano
nano alembic.ini
---> sqlalchemy.url = postgresql+psycopg2://postgres:postgres@postgres:5432/postgres

echo '0 0 * * * python /opt/billing/cli.py check_new_free_orders' > /etc/cron.d/cronfile.cronjob
echo '0 0 * * * python /opt/billing/cli.py check_new_orders' > /etc/cron.d/cronfile.cronjob
echo '0 0 * * * python /opt/billing/cli.py check_active_recurent_orders' > /etc/cron.d/cronfile.cronjob
echo '0 0 * * * python /opt/billing/cli.py check_expired_orders' > /etc/cron.d/cronfile.cronjob

chmod 0644 /etc/cron.d/cronfile.cronjob
crontab /etc/cron.d/cronfile.cronjob
touch /var/log/cron.log
cron -f &
```

## Авторы

[stas-chuprinskiy](https://github.com/stas-chuprinskiy),
[olegtsss](https://github.com/olegtsss)
