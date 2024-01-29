"""Entrypoint for the redisflow package."""

from redisflow.app import app

app.worker_main(argv=["worker", "--loglevel=INFO"])
