"""WSGI entry point for Gunicorn."""
from cookgpt import create_app_wsgi

app = application = create_app_wsgi()  # noqa
