# praktikum_new_diplom



repo_owner: Nikita-Makkar
kittygram_domain: https://kittygram-212.ddns.net/
taski_domain: https://magic-212.ddns.net/
dockerhub_username: nikita212212


Напишите докерфайл с Django-проектом и Gunicorn. В конце сборки контейнера должны быть команды для миграции и сборки статики.
Напишите docker-compose, в нём опишите запуск контейнеров из официальных образов PostgreSQL и nginx и своего контейнера с проектом. Опишите конфигурацию контейнеров.
Запушьте контейнер с проектом на Docker Hub.
Разверните контейнеры на своём удалённом виртуальном сервере.
Добавьте в файл README.md адрес сервера, на котором запущен ваш проект (укажите IP или доменное имя), а также логин и пароль администратора. Это нужно, чтобы ревьюер смог проверить работу админки.
Добавьте в файл README.md адрес сервера, на котором запущен ваш проект
 (укажите IP или доменное имя), а также логин и пароль администратора. Это нужно, чтобы ревьюер смог проверить работу админки.

docker compose up

backend docker exec -it infra-backend-1 bash

Создайте и примените миграции:

`python3 manage.py makemigrations
python manage.py migrate`

 ./python3 manage.py migrate


 ./python3 manage.py collectstatic

 ./python3 manage.py createsuperuser

 python3 manage.py import_data ingredients.csv
