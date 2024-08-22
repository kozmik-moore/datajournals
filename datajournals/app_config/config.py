import json
from os import mkdir, getcwd
from os.path import join, abspath, dirname, exists

from datajournals.authorization.init_db import init_default_roles
from datajournals.dreamdb.init_db import init_default_dream_tags
from datajournals.journaldb.init_db import init_default_journal_tags, init_journal_attachments_store
from datajournals.restaurantdb.init_db import init_default_restaurant_tags
from datajournals.sleepdb.init_db import init_default_sleep_tags
from datajournals.tests import healthmodel
from datajournals.tests import gamingmodel
from instance.config import DATABASE_URI, ATTACHMENTS

appdir = abspath(join(dirname(__file__), '../..'))
current_dir = abspath(getcwd())
instance_dir = abspath(join(current_dir, 'instance'))
JSON_PATH = abspath(join(instance_dir, 'config.json'))
attachments_dir = abspath(join(current_dir, 'attachments'))


class Config(object):
    SECRET_KEY = '9efdc4acf5de2e3b5dcf8a2322e41a024ae72504ad06e191'
    TRACK_MODIFICATIONS = False
    JOURNAL_ATTACHMENTS_DIR = join(attachments_dir, 'journaldb')
    HEALTH_ATTACHMENTS_DIR = join(attachments_dir, 'healthdb')


class TestingConfig(Config):
    Testing = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = DATABASE_URI or 'sqlite:///' + join(appdir, 'app_dev.db')
    if ATTACHMENTS:
        JOURNAL_ATTACHMENTS_DIR = abspath(join(ATTACHMENTS, 'journaldb'))
        HEALTH_ATTACHMENTS_DIR = abspath(join(ATTACHMENTS, 'healthdb'))


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = DATABASE_URI or 'sqlite:///' + join(appdir, 'data_journals.db')
    if ATTACHMENTS:
        JOURNAL_ATTACHMENTS_DIR = abspath(join(ATTACHMENTS, 'journaldb'))
        HEALTH_ATTACHMENTS_DIR = abspath(join(ATTACHMENTS, 'healthdb'))


config = {
    'testing': TestingConfig,
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

DB_INIT_MAP = {
    'AUTHORIZATION': init_default_roles,
    'DREAMDB': init_default_dream_tags,
    'JOURNALDB': init_default_journal_tags,
    'RESTAURANTDB': init_default_restaurant_tags,
    'SLEEPDB': init_default_sleep_tags,
    'HEALTHDB': healthmodel.set_default_tags,
    'GAMINGDB': gamingmodel.set_default_tags,
}

ATT_INIT_MAP = {
    'JOURNALDB': init_journal_attachments_store,
    'HEALTHDB': healthmodel.init_folder
}


def create_init_file():
    if not exists(instance_dir):
        mkdir(instance_dir)
        open(abspath(join(instance_dir, '__init__.py'))).close()
    if not exists(JSON_PATH):
        db_list = []
        att_dir_list = []
        json_dict = {
            'DATABASE': {},
            'ATTACHMENTS DIRS': {}
        }

        for name in DB_INIT_MAP.keys():
            db_list.append(name)
        for name in ATT_INIT_MAP.keys():
            att_dir_list.append(name)

        db_list = sorted(db_list)
        att_dir_list = sorted(att_dir_list)
        for component in db_list:
            json_dict['DATABASE'][component] = False
        for component in att_dir_list:
            json_dict['ATTACHMENTS DIRS'][component] = False

        with open(JSON_PATH, 'w') as f:
            json.dump(json_dict, f, indent=4)


def run_init_config():
    """
    Checks for the json file tracking tags initialization for each database.
    Then checks that each database has initialized its tags. Runs init function(s) if not.
    :return:
    """
    create_init_file()

    with open(JSON_PATH) as rf:
        json_dict = json.load(rf)

        section = json_dict['DATABASE']
        keys = section.keys()
        for key in DB_INIT_MAP.keys():
            if key not in keys or not section[key]:
                DB_INIT_MAP[key]()
                section[key] = True

        section = json_dict['ATTACHMENTS DIRS']
        keys = section.keys()
        for key in ATT_INIT_MAP.keys():
            if key not in keys or not section[key]:
                ATT_INIT_MAP[key]()
                section[key] = True

        with open(JSON_PATH, 'w') as wf:
            json.dump(json_dict, wf, indent=4)
