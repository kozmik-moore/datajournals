import random
from datetime import datetime
from os import mkdir
from os.path import abspath, join, dirname, exists
from random import randint, choice
from shutil import rmtree


class BaseModelTest:
    def __init__(self, **kwargs):

        self._fill_tables_func = kwargs.get('fill_tables_func')
        self._init_tables_func = kwargs.get('init_tables')
        self._set_tags_func = kwargs.get('set_tags')
        self._create_tables_on_init = kwargs.get('create_tables_on_init', True)
        self._init_tables_on_fill = kwargs.get('init_tables_on_fill', True)
        self._set_tags_on_fill = kwargs.get('set_tags_on_fill', True)

    @property
    def fill_tables_func(self):
        return self._fill_tables_func

    @fill_tables_func.setter
    def fill_tables_func(self, func):
        self._fill_tables_func = func

    @property
    def init_tables_func(self):
        return self._init_tables_func

    @init_tables_func.setter
    def init_tables_func(self, func):
        self._init_tables_func = func

    @property
    def set_tags_func(self):
        return self._set_tags_func

    @set_tags_func.setter
    def set_tags_func(self, func):
        self._set_tags_func = func

    @property
    def init_on_fill(self):
        return self._init_tables_on_fill

    @init_on_fill.setter
    def init_on_fill(self, value: bool):
        if type(value) == bool:
            self._init_tables_on_fill = value

    @property
    def create_on_init(self):
        return self._create_tables_on_init

    @create_on_init.setter
    def create_on_init(self, value: bool):
        if type(value) == bool:
            self._create_tables_on_init = value

    @property
    def set_tags_on_fill(self):
        return self._set_tags_on_fill

    @set_tags_on_fill.setter
    def set_tags_on_fill(self, value: bool):
        if type(value) == bool:
            self._set_tags_on_fill = value

    def fill_tables(self, num_records: int = 20, init_tables=None, set_tags=None):
        """
        Calls function to fill tables.
        Checks method args for overriding behavior. Then checks internal settings.
        :param num_records: number of records to fill table with
        :param init_tables: If True, initializes tables, regardless of internal setting
        :param set_tags: If True, sets default table tags, regardless of internal setting
        :return:
        """
        if init_tables is not None:
            if type(init_tables) == bool and init_tables:
                self.init_tables_func()
            elif type(init_tables) != bool:
                raise TypeError('init_tables is not of type bool')
        elif self.init_on_fill:
            self.init_tables_func()
        if set_tags is not None:
            if type(set_tags) == bool and set_tags:
                self.set_tags_func()
            elif type(set_tags) != bool:
                raise TypeError('set_tags is not of type bool')
        elif self.set_tags_on_fill:
            self._set_tags_func()
        self.fill_tables_func(num_records)

    def init_tables(self, create_tables=None):
        """
        Calls function to initialize tables.
        Checks method args for overriding behavior. Then checks internal settings.
        :param create_tables: If True, creates new tables, regardless of internal setting
        :return:
        """
        if create_tables is not None:
            if type(create_tables) == bool:
                self.init_tables_func(create_tables)
        else:
            self.init_tables_func(self.create_on_init)

    def set_default_tags(self, init_tables=False):
        """
        Adds the default tags to the table.
        :param init_tables: Determines whether to create new tables.
        :return:
        """
        if init_tables:
            self.init_tables(True)
        self.set_tags_func()

    # TODO add methods for handling folders, if applicable


def get_random_datetime(min_: datetime = None,
                        max_: datetime = None):
    """
    Creates a random datetime between min_ and max_.
    If min_ is not set, then the minimum possible datetime will be set to the new year of 2020.
    If max_ is not set, then the maximum possible datetime will be datetime.now().

    :return: a random datetime object
    """

    # Check parameters and set limits for range of random selection
    min_set = True
    max_set = True
    if min_ is not None:
        if type(min_) is not datetime:
            raise TypeError('min_ must be None or of type datetime')
    else:
        min_set = False
        min_ = datetime(2020, 1, 1)
    if max_ is not None:
        if type(max_) is not datetime:
            raise TypeError('max_ must be None or of type datetime')
    else:
        max_set = False
        max_ = datetime.now()
    if min_ > max_:
        if min_set and not max_set:
            raise ValueError('set a max_ greater than min_')
        elif max_set and not min_set:
            raise ValueError('set a min_ less than max_')
        elif max_set and min_set:
            raise ValueError('min is greater than max')

    dt = datetime.fromtimestamp(
        randint(
            int(min_.replace(microsecond=0).timestamp()),
            int(max_.replace(microsecond=0).timestamp())
        )
    )
    return dt


def create_test_attachments(number: int = 5):
    path = abspath(join(dirname(__file__), 'attachments'))
    if exists(path):
        rmtree(path=path, ignore_errors=True)
    mkdir(path)

    attachment_descriptions = ["happy", "sad", "hungry", "sexy", "powerful"]
    tmp = attachment_descriptions.copy()
    for i in range(number):
        text = (f'This is attachment {i + 1}. '
                f'It is a {tmp.pop(randint(0, len(tmp) - 1)) if tmp else choice(attachment_descriptions)} attachment.')
        with open(abspath(join(path, f'attachment {i + 1}.txt')), 'w') as f:
            f.write(text)


# TODO add more features for controlling beginning, end, and min and max length of the text returned
def get_random_text(text: str = None):
    """
    Returns a random slice of text
    :param text: an optional user-supplied string of text
    :return: a string of text sliced from either a user supplied string or a default one
    """
    li = ('Dolor modi consequatur accusantium. Iusto laboriosam totam aperiam. Cupiditate ab occaecati molestiae '
          'ut et molestiae. Nobis aut velit quaerat repellat soluta excepturi. Fugit eos nemo voluptates natus. '
          'Modi corporis eos rem sed provident. Est corporis dolorum natus aut nemo sequi nam. Qui eos ut quas ea '
          'aut est. Voluptatem quia minima unde ducimus. Adipisci et aut nemo culpa dolorem assumenda. Et quae '
          'reprehenderit voluptatibus non quas commodi et distinctio. Quae quibusdam et sed ut in aut. Iusto ut '
          'et eum. Id enim beatae sit praesentium aut. Vel suscipit ipsum nihil. Facere aliquam iste nulla '
          'consequatur. Et hic ratione eum aut. Dolor saepe nihil cum quibusdam et quibusdam. Similique omnis '
          'quasi sit qui cupiditate rerum vitae vero. Expedita natus aut natus at voluptatem debitis esse.')
    if text:
        li = text
    maxlen = len(li) - 1
    bs = random.randint(0, maxlen)
    es = random.randint(bs, maxlen)
    rc = f'{"..." if bs != 0 else ""}{li[bs: es]}{"..." if es != len(li) - 1 else ""}'

    return rc
