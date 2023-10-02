release: ./make_release
web: gunicorn -c gunicorn.conf.py
worker: celery -A redisflow.app worker -P solo -l INFO