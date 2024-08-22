from os import mkdir, getcwd
from os.path import abspath, join, exists

log_dir = abspath(join(getcwd(), 'logs'))
if not exists(log_dir):
    mkdir(log_dir)
log_path = abspath(join(log_dir, 'datajournals.log'))

log_dict = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] [%(levelname)s | %(module)s] %(message)s',
            'datefmt': '%b %d, %Y %H:%M:%S (%a)',
        }
    },
    'handlers': {
        'time-rotate': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': log_path,
            'when': 'W0',
            'interval': 1,
            'backupCount': 3,
            'formatter': 'default',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default'
        }
    },
    'filters': {},
    'loggers': {
        '': {  # root logger
            'level': 'INFO',  # TODO does not seem to actually set level
            'handlers': ['time-rotate', 'console']
        }
    }
}
