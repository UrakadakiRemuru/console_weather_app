import os

import django
from django.core.management import call_command


def setup_django():
    '''
    Настраивает Django, выполняет миграции и инициализацию базы данных.
    '''
    call_command('makemigrations', verbosity=0)
    call_command('migrate', verbosity=0)
