"""This module is used to initialize the celery app and the web app."""
from cookgpt import create_app_wsgi
from redisflow import celeryapp as app

webapp = create_app_wsgi()
app.init_app(webapp)
