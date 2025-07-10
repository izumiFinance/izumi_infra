# -*- coding: utf-8 -*-
import logging
import sys
from functools import wraps
from celery.app.control import Control
from celery_once import QueueOnce, AlreadyQueued
from celery import current_task

from izumi_infra.utils.cache_util import FAIL_BACK_RENEWAL_MANAGER, RenewalManager

logger = logging.getLogger(__name__)

def is_celery_worker_mode():
    return sys.argv and sys.argv[0].endswith('celery') and 'worker' in sys.argv

def is_celery_beat_mode():
    return sys.argv and sys.argv[0].endswith('celery') and 'beat' in sys.argv


def sequence_task(func):
    """
    Limit to single task instance at a time, require: @shared_task(bind=True)
    This wrapper may be slow, not suggest to use
    https://stackoverflow.com/questions/20894771/celery-beat-limit-to-single-task-instance-at-a-time
    """

    task_name = f'{func.__module__}.{func.__name__}'

    @wraps(func)
    def wrapped(self, *args, **kwargs):
        control : Control = self.app.control
        workers = control.inspect().active()

        for worker, tasks in workers.items():
            for task in tasks:
                if (task_name == task['name'] and
                        self.request.id != task['id'] and
                        tuple(args) == tuple(task['args']) and
                        kwargs == task['kwargs']
                    ):
                    # control.revoke task occur ERROR
                    logger.critical(f'sequence limit task: {task_name} ({args}, {kwargs}) is running on {worker}, skipping')

                    return None

        return func(self, *args, **kwargs)

    return wrapped

def clean_celery_once_redis_lock():
    once_redis = QueueOnce().once_backend.redis
    # worker crash down, lock still exist
    # TODO maybe fatal error when one of multi worker crash
    for key in once_redis.scan_iter("qo_*"):
        logger.warning(f'clean celery once key: {key}')
        once_redis.delete(key)

class IzumiQueueOnce(QueueOnce):
    def apply_async(self, args=None, kwargs=None, **options):
        once_options = options.get('once', {})
        # get call or task config
        log_critical = once_options.get('log_critical', self.once.get('log_critical', True))
        try:
            return super(IzumiQueueOnce, self).apply_async(args, kwargs, **options)
        except AlreadyQueued as e:
            if log_critical:
                logger.critical(f'IzumiQueueOnce base task: {self.name} is not finished yet, try run another instance')
            raise e

    def __call__(self, *args, **kwargs):
        key = self.get_key(args, kwargs)
        # TODO use IzumiQueueOnce TTL and enable params
        self.request.lock_renewal = RenewalManager(
            key=key,
            redis_instance=QueueOnce().once_backend.redis,
            initial_ttl=20 * 60
        )

        return super().__call__(*args, **kwargs)

def current_task_lock_renewal() -> RenewalManager:
    try:
        return current_task.request.lock_renewal
    except Exception as e:
        logger.exception(e)
        return FAIL_BACK_RENEWAL_MANAGER
