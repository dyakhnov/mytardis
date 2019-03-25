import os
import urllib
import yaml
from .default_settings import *

settings_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'settings.yaml')
if os.path.isfile(settings_filename):
    with open(settings_filename) as settings_file:
        data = yaml.load(settings_file, Loader=yaml.FullLoader)

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

    CELERY_RESULT_BACKEND = 'amqp'
    BROKER_URL = 'amqp://%(user)s:%(password)s@%(host)s:5672/%(vhost)s' % {
        'host': data['rabbitmq']['host'],
        'user': data['rabbitmq']['user'],
        'password': urllib.quote_plus(data['rabbitmq']['password'],),
        'vhost': data['rabbitmq']['vhost']
    }

    DEFAULT_STORAGE_BASE_DIR = data['default_store_path']
    METADATA_STORE_PATH = data['metadata_store_path']

STATIC_ROOT = '/srv/stormon-cinder-staging3/static_files'

CELERY_QUEUES += (
    Queue('filters', Exchange('filters'),
          routing_key='filters',
          queue_arguments={'x-max-priority': MAX_TASK_PRIORITY}),
)

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
