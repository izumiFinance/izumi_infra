# -*- coding: utf-8 -*-
from django.db import connections

def close_old_connections(**kwargs):
    for conn in connections.all():
        conn.close_if_unusable_or_obsolete()
