import os

# Project folder
PROJECT_DIR = os.getcwd()

# Logging configurations.
LOGGING_CONFIG = dict(
    version=1,
    formatters={
        'general': {'format': '%(asctime)s %(levelname)s %(message)s'}
    },
    handlers={
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'general',
            'level': 'DEBUG'
        },
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'general',
            'level': 'DEBUG',
            'filename': 'logs/logfile.log',
            'mode': 'a'}
    },
    root={
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
)
