from cookgpt import create_app_wsgi
from redisflow import celeryapp as app

webapp = create_app_wsgi()
app.init_app(webapp)
