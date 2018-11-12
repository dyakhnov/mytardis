# pylint: disable=wildcard-import,unused-wildcard-import
from tardis.test_settings import *  # noqa # pylint: disable=W0401,W0614

DATABASES = {
    'default': {
        'ENGINE':   "django.db.backends.postgresql_psycopg2",
        'NAME':     "postgres",
        'USER':     "user",
        'PASSWORD': "password",
        'HOST':     "db",
        'PORT':     "5432",
    }
}

DEFAULT_STORAGE_BASE_DIR = "/var/store"
