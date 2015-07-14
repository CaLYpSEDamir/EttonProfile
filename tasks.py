# coding: utf-8

import os

from celery import Celery


celery = Celery("tasks", broker="amqp://")
celery.conf.CELERY_RESULT_BACKEND = os.environ.get(
    'CELERY_RESULT_BACKEND', 'amqp')


@celery.task
def save_event(user_id, date, time, text):
    return user_id, date, time, text

# celery.start('celery -A tasks worker')