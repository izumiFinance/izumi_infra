# -*- coding: utf-8 -*-
from django.db import connections
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from django.db import connection
from django.core.paginator import Paginator

def close_old_connections(**kwargs):
    for conn in connections.all():
        conn.close_if_unusable_or_obsolete()

class DjangoDbConnSafeThreadPoolExecutor(ThreadPoolExecutor):
    """
    When a function is passed into the ThreadPoolExecutor via either submit() or map(),
    this will wrap the function, and make sure that close_django_db_connection() is called
    inside the thread when it's finished so Django doesn't leak DB connections.

    Since map() calls submit(), only submit() needs to be overwritten.
    """
    def close_django_db_connection(self):
        connection.close()

    def generate_thread_closing_wrapper(self, fn):
        @wraps(fn)
        def new_func(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            finally:
                self.close_django_db_connection()
        return new_func

    def submit(*args, **kwargs):
        """
        I took the args filtering/unpacking logic from

        https://github.com/python/cpython/blob/3.7/Lib/concurrent/futures/thread.py

        so I can properly get the function object the same way it was done there.
        """
        if len(args) >= 2:
            self, fn, *args = args
            fn = self.generate_thread_closing_wrapper(fn=fn)
        elif not args:
            raise TypeError("descriptor 'submit' of 'ThreadPoolExecutor' object "
                        "needs an argument")
        elif 'fn' in kwargs:
            fn = self.generate_thread_closing_wrapper(fn=kwargs.pop('fn'))
            self, *args = args

        return super(self.__class__, self).submit(fn, *args, **kwargs)

def chunked_iterator(queryset, chunk_size=2000):
    """
    MySQL do not support streaming results for code: XxxModel.objects.all().iterator()
    https://docs.djangoproject.com/en/4.1/ref/models/querysets/#without-server-side-cursors
    """
    paginator = Paginator(queryset, chunk_size)
    for page in range(1, paginator.num_pages + 1):
        for obj in paginator.page(page).object_list:
            yield obj
