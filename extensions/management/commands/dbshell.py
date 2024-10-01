# -*- coding: utf-8 -*-
from typing import Callable
import shutil

from django.db import connections
from django.core.management.commands import dbshell
from django.db.backends.mysql.base import DatabaseWrapper
from django.db.backends.mysql.client import DatabaseClient

class MyCLIDatabaseClient:
    # https://www.mycli.net/
    executable_name = 'mycli'
    super_settings_to_cmd_args_env: Callable

    param_fix_mapping = {
        '--default-character-set=': '--charset='
    }

    @classmethod
    def settings_to_cmd_args_env(cls, settings_dict, parameters):
        args, env = cls.super_settings_to_cmd_args_env(settings_dict, parameters)
        # fix param diff
        for i in range(len(args)):
            for key in cls.param_fix_mapping.keys():
                if args[i].startswith(key): args[i] = args[i].replace(key, cls.param_fix_mapping[key])
        return args, env

    @classmethod
    def wrapper(cls, kls: DatabaseClient):
        kls.executable_name = cls.executable_name
        cls.super_settings_to_cmd_args_env = kls.settings_to_cmd_args_env
        kls.settings_to_cmd_args_env = cls.settings_to_cmd_args_env

class Command(dbshell.Command):
    help = (
        "Runs a database interactive interpreter. Tries to use mycli"
        ", if one of them is available. Any standard input is executed "
        "as code."
    )

    def handle(self, **options):
        connection: DatabaseWrapper = connections[options.get('database')]
        if connection.vendor == 'mysql' and shutil.which(MyCLIDatabaseClient.executable_name) is not None:
            MyCLIDatabaseClient.wrapper(DatabaseClient)

        super(Command, self).handle(**options)
