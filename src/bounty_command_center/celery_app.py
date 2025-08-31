from celery import Celery
from .config import settings

celery_app = Celery(
    "bounty_command_center",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
    include=["bounty_command_center.tasks"],
)

from celery.schedules import crontab

celery_app.conf.update(
    task_track_started=True,
    beat_schedule={
        "scan-new-targets-every-minute": {
            "task": "bounty_command_center.tasks.scan_new_targets",
            "schedule": 60.0,  # Run every 60 seconds
        },
        "rescan-all-targets-daily": {
            "task": "bounty_command_center.tasks.rescan_all_targets",
            "schedule": 86400.0,  # Run every 24 hours (24 * 60 * 60)
        },
        "harvest-all-platforms-every-6-hours": {
            "task": "bounty_command_center.tasks.schedule_all_platform_harvests",
            "schedule": crontab(minute=0, hour='*/6'),
        },
    },
)
