# -*- coding: utf-8 -*-
import os
import logging

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import management

import MySQLdb as Database

class Command(BaseCommand):
    help = 'Remove migrations file, rm db and tables, execute makemirgations and migrate, loaddata from fixtrues'

    def handle(self, *args, **options):
        db_info = settings.DATABASES.get('default')
        database_host = db_info.get('HOST')
        database_port = db_info.get('PORT')
        database_name = db_info.get('NAME')
        user = db_info.get('USER')
        password = db_info.get('PASSWORD')

        i = input("Reset db:{} at {}:{}, continue? [y/N]: ".format(database_name, database_host, database_port))
        if i != 'y':
            print("reset cancel")
            return

        kwargs = {
            'user': user,
            'passwd': password,
        }
        if database_host.startswith('/'):
            kwargs['unix_socket'] = database_host
        else:
            kwargs['host'] = database_host

        if database_port:
            kwargs['port'] = int(database_port)

        logging.info('Remove migrations files')
        os.system('find . -path "*/migrations/*.py" -not -name "__init__.py" -delete')
        os.system('find . -path "*/migrations/*.pyc"  -delete')

        # create new database
        connection = Database.connect(**kwargs)
        # CREATE DATABASE IF NOT EXISTS izumi CHARACTER SET utf8mb4;
        drop_query = 'DROP DATABASE IF EXISTS `%s`' % database_name
        create_query = 'CREATE DATABASE `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci' % database_name
        logging.info('Executing... "%s"', drop_query)
        connection.query(drop_query)
        logging.info('Executing... "%s"', create_query)
        connection.query(create_query.strip())

        logging.info('Start initial project table and superuser')
        management.call_command('makemigrations')
        management.call_command('migrate')
        management.call_command('createsuperuser')

        # TODO load fixture data or export config fixture before clean
