# -*- coding: utf-8 -*-
import os
import logging

from django.core.management.base import BaseCommand, CommandParser
from apps.utils.abi_types_generator import abiTypesGenerator

class Command(BaseCommand):
    help = 'Generate python type dict class define file from contract abi'

    def add_arguments(self, parser: CommandParser) -> None:
        super().add_arguments(parser)
        parser.add_argument('files', nargs='*', help="abi json file path")

    def handle(self, *args, **options):
        # TODO for loop detect json file and gen or by cli param
        files = options['files']
        for file_path in files:
            with open(file_path, 'r') as f:
                print(abiTypesGenerator(f.read()))
