# pylint: disable=wildcard-import,unused-wildcard-import
from tardis.test_settings import *  # noqa # pylint: disable=W0401,W0614

DATABASES = {
    'default': {
        'ENGINE':   "django.db.backends.mysql",
        'NAME':     "mytardis",
        'USER':     "root",
        'PASSWORD': "mysql",
        'HOST':     "127.0.0.1", # localhost will force client to use socket, rather than TCP
        'PORT':     "3306",
        'STORAGE_ENGINE':   "InnoDB",
        'OPTIONS': {
            'init_command': 'SET default_storage_engine=InnoDB',
            'charset':      'utf8',
            'use_unicode':  True,
        },
    },
}
