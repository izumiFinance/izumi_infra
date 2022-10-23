import sys

def is_celery_worker_mode():
    return sys.argv and sys.argv[0].endswith('celery') and 'worker' in sys.argv
