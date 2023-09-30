release: ./make_release
web: gunicorn -c gunicorn.conf.py
worker: celery --app=redisflow.app worker --pool=solo