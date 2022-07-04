### Backend project for KMS

This is a python web backend project for KMS using Django 4.0.5 and Django Rest Framework 3.13.1.

If you are not so familiar with Django I encourage you to go through the tutorial at https://docs.djangoproject.com/en/4.0/intro/tutorial01/

If you are not so familiar with Django Rest Framework I encourage you to go through the tutorial at https://www.django-rest-framework.org/tutorial/1-serialization/

The reason why I choose Django as our web backend project is because this a POC project and I don't want to spend too much time on it. And Django provides lots of out of box functionality which can reduce lots of development efforts compared with Flask.



### Folder Structure

- manager.py: python file under home folder, this file should not be changed and this is a helper file to run Django commands
- kms_backend: project folder contains project settings in **settings.py** and URL mapping in **urls.py**
- image: image application folder contains, image application related files
-            - admin.py: admin login related sett ups
             - models.py: database and object mapping class (ORM)
             - serialiazers.py: serialiazer class used by Django Rest Framework
             - views.py: class to store the API endpoint and logic



### Common commands

| Command                               | description                                       |
| ------------------------------------- | ------------------------------------------------- |
| django-admin startproject kms_backend | Django command to create current project(one off) |
| python manage.py startapp image       | Django command to create application(one off)     |
| python manage.py makemigration        | Create migration file                             |
| python manage.py migrate              | Run migration file to create/update/delete tables |
| python manage.py runserver            | Start Django application in development mode      |
|                                       |                                                   |
|                                       |                                                   |
|                                       |                                                   |



### API

API endpoint for development -> http://127.0.0.1:8000/api/

![api_summary](https://github.com/Qucy/kms_backend/blob/master/api_summary.jpg)

![image_tag_api_list](https://github.com/Qucy/kms_backend/blob/master/image_tag_api_list.jpg)

![image_tag_api_add](https://github.com/Qucy/kms_backend/blob/master/image_tag_api_add.jpg)