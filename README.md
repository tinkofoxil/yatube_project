# yatube_project
Социальная сеть блогеров
### Технологии
Python 3.7
Django 2.2.19
pytz==2021.3
sqlparse==0.4.2
### Запуск проекта в dev-режиме
- Установите и активируйте виртуальное окружение
- Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
``` 
- В папке с файлом manage.py выполните команды:
```
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py runserver
``` 