from typing import TYPE_CHECKING, Type, cast

import celery.app.base as celerybase

from cookgpt import logging

if TYPE_CHECKING:
    from cookgpt.app import App as WebApp


class Celery(celerybase.Celery):
    """Celery app"""

    webapp: "WebApp"

    def init_app(self, app: "WebApp"):
        """initialize celery"""

        if hasattr(self, "webapp"):
            logging.debug("Celery already initialized")
            return

        logging.info("Initializing celery")
        self.webapp = app
        logging.info("Setting celery config")
        self.conf.update(app.config.get_namespace("CELERY_"))
        logging.info("Setting celery task base")
        TaskBase = cast(Type, self.Task)
        all_tasks = list(app.config.CELERY_TASKS)
        logging.info("Autodiscovering tasks: %r", all_tasks)
        self.autodiscover_tasks(all_tasks, force=True)

        class ContextTask(TaskBase):  # type: ignore
            """Task that run within app context"""

            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)

        self.Task = ContextTask


celeryapp = Celery("cookgpt")
