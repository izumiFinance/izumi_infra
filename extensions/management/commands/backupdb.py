# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate python type dict class define file from contract abi'

    def add_arguments(self, parser: CommandParser) -> None:
        super().add_arguments(parser)
        parser.add_argument('files', nargs='*', help="abi json file path")

    def handle(self, *args, **options):
        db_info = settings.DATABASES.get('default')
        database_host = db_info.get('HOST')
        database_port = db_info.get('PORT')
        database_name = db_info.get('NAME')
        user = db_info.get('USER')
        password = db_info.get('PASSWORD')

        main_args = []
        main_args.append('--databases %s' % database_name)
        main_args.append('--user=%s' % user)

        if password:
            main_args.append('--password=%s' % password)

        if database_host:
            main_args.append('--host=%s' % database_host)

        if database_port:
            main_args.append('--port=%s' % database_port)

        command = 'mysqldump %s' % (' '.join(main_args))
        backup_path = f'../volumes/backup/{database_name}-{datetime.strftime(datetime.now(), "%Y-%m-%d_%H-%M-%S")}.sql'
        final_cmd = command + ' > ' + backup_path

        logging.info(f'execute: {final_cmd} ...')
        os.system(final_cmd)
