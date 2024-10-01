# -*- coding: utf-8 -*-
import subprocess
import shutil
import logging

from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'use iredis connect to BROKER_URL for management'

    def handle(self, *args, **options):
        if shutil.which('iredis') is None:
            logging.info(f'iredis is not install, please install with version according to requirements.txt')
            return

        args = ['iredis', '--url', settings.BROKER_URL]
        logging.info(f'try use iredis connect: {settings.BROKER_URL} ...')
        subprocess.run(args, check=True)
