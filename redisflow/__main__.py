from redisflow.app import app

app.worker_main(argv=["worker", "--loglevel=INFO"])
