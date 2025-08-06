import logging
import logging.config
from app.config.settings import settings

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(funcName)s(): %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': settings.log_level,
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': settings.log_file if settings.log_file else 'app.log',
            'mode': 'a',
            'formatter': 'detailed',
            'level': settings.log_level,
        },
    },
    'root': {
        'handlers': ['console', 'file'] if settings.log_file else ['console'],
        'level': settings.log_level,
        'propagate': True,
    },
}

def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
