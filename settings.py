import os
import urllib
import yaml
from .default_settings import *

data = yaml.load(os.environ.get('SETTINGS'))

DEBUG = data['debug']
SECRET_KEY = data['secret_key']

DATABASES['default'] = {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'HOST': data['postgres']['host'],
    'PORT': data['postgres']['port'],
    'USER': data['postgres']['user'],
    'PASSWORD': data['postgres']['password'],
    'NAME': data['postgres']['name']
}

STATIC_ROOT = '/mnt/static_files'

CELERY_RESULT_BACKEND = 'amqp'
BROKER_URL = 'amqp://%(user)s:%(password)s@%(host)s:5672/%(vhost)s' % {
    'host': data['rabbitmq']['host'],
    'user': data['rabbitmq']['user'],
    'password': urllib.quote_plus(data['rabbitmq']['password'],),
    'vhost': data['rabbitmq']['vhost']
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
        'django': {
            'format': 'django: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'level': 'ERROR',
            'facility': 'user',
            'formatter': 'django'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'syslog'],
            'level': 'ERROR'
        },
    }
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
DEFAULT_ARCHIVE_FORMATS = ['tar']
REDIS_VERIFY_MANAGER = False

# Clear a few global vars
def del_if_set(name):
    if name in globals():
        del(globals()[name])
del_if_set('EMAIL_PORT')
del_if_set('EMAIL_HOST')
del_if_set('EMAIL_HOST_USER')
del_if_set('EMAIL_HOST_PASSWORD')
del_if_set('EMAIL_USE_TLS')
