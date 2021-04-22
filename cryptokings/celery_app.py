from core.common import django_settings
import os
from cryptokings.settings import CELERY_BROKER_URL, TIME_ZONE
from celery.schedules import crontab
from celery import Celery
from cryptokings.tasks import everydayat0, every15mins, every6hours

app = Celery('cryptokings', broker=CELERY_BROKER_URL, backend=CELERY_BROKER_URL)
app.conf.timezone = TIME_ZONE

@app.task
def _everydayat0():
    everydayat0()
    return True

@app.task
def _every6hours():
    every6hours()
    return True

@app.task
def _every15mins():
    every15mins()
    return True


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute=0, hour=0),
        _everydayat0.s()
    )

    sender.add_periodic_task(
        crontab(minute="*/15"),
        _every15mins.s()
    )

    sender.add_periodic_task(
        crontab(minute=1, hour="*/6"),
        _every6hours.s()
    )


if __name__ == "__main__":
    app.start()