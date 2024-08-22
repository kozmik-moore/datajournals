from datajournals.tests.testbase import *
from datajournals.tests.sleepmodel import *
from datajournals.tests.dreammodel import *
from datajournals.tests.journalmodel import *
from datajournals.tests.restaurantmodel import *
from datajournals.tests.authorizationmodel import *
from datajournals.tests.healthmodel import *
from datajournals.tests.gamingmodel import *


def fill_all_tables(init_tables: bool = False, set_default_tags: bool = False, num_records: int = 20):
    """
    Fills all tables with fictional data.
    :param init_tables: flag which determines whether all tables will be dropped and re-created
    :param set_default_tags: flag which determines whether all tables will be populated with default tags
    :param num_records: where applicable, flag which determines how many records will be created
    """
    fill_dream_tables(init_tables, set_default_tags, num_records)
    fill_sleep_tables(init_tables, set_default_tags, num_records)
    fill_journal_tables(init_tables, set_default_tags, num_records)
    fill_restaurant_tables(init_tables, set_default_tags)
    fill_authorization_tables(init_tables, set_default_tags)
    healthmodel.fill_tables(init_tables, set_default_tags)
    gamingmodel.fill_tables(init_tables, set_default_tags)
    print('All db tables filled with data.')


def clear_all_tables():
    """
    Clears all database tables and associated folders. Checks via console whether user really desires this.
    USE WITH CAUTION. WILL DELETE ALL DATA.
    """
    def clear(create_tables=False):
        init_dream_tables(create_tables)
        init_journal_tables(create_tables)
        init_journal_attachments_store(True)
        init_restaurant_tables(create_tables)
        init_sleep_tables(create_tables)
        init_authorization_tables(create_tables)
        healthmodel.init_tables(create_tables)
        healthmodel.init_folder()
        gamingmodel.init_tables()
    input_ = input('Are you sure you wish to delete all tables? [yes/no] ')
    if input_ in ['yy', 'YY', 'YES']:
        clear()
        print('All db tables cleared.')
    elif input_ in ['yes', 'Yes']:
        if input('Are you really sure? [yes/no] ') in ['yes', 'Yes', 'YES']:
            clear()
            print('All db tables cleared.')
        else:
            print('Aborting call to clear tables.')
    elif input_ in ['no', 'No', 'n', 'N']:
        print('Aborting call to clear tables.')
    else:
        print(f'Invalid input: {input_}. Aborting call to clear tables.')
