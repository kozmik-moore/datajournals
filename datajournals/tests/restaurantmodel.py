from random import choice, randint

from datajournals import db
from datajournals.models import RestaurantTag, RestaurantRecord, RestaurantVisit, RestaurantNote
from datajournals.restaurantdb.init_db import init_restaurant_tables, init_default_restaurant_tags
from datajournals.tests import get_random_datetime


def fill_restaurant_tables(init: bool = False, set_default_tags: bool = False):

    # Reinitialize tables
    if init:
        init_restaurant_tables()
    if set_default_tags:
        init_default_restaurant_tags()

    # Create tags
    db_tags = db.session.query(RestaurantTag.tag).all()
    food_list = ['pizza', 'tacos', 'burritos', 'burgers', 'sandwiches', 'drinks', 'coffee', 'ice cream']
    food_tags = []
    for food in food_list:
        if (food,) in db_tags:
            food_tags.append(RestaurantTag.query.filter_by(tag=food).first())
        else:
            food_tags.append(RestaurantTag(tag=food))

    type_list = ['fast-food', 'dine-in', 'takout']
    type_tags = []
    for type_ in type_list:
        if (type_,) in db_tags:
            type_tags.append(RestaurantTag.query.filter_by(tag=type_).first())
        else:
            type_tags.append(RestaurantTag(tag=type_))

    restaurant_names = ['Sally\'s',
                        'Jerry\'s Kitchen',
                        'Alfred\'s Place',
                        'The Place',
                        'The Happening',
                        'Brother\'s',
                        'Hedgehog Heaven',
                        'Food Smithy',
                        'The Foodery',
                        'Rip It!',
                        'Aria\'s Bouduoir',
                        ]

    # Initialize Restaurant object lists
    restaurants = []
    visits = []
    notes = []

    # Create Restaurant objects with description and tags data and store in list
    for name in restaurant_names:
        description = f'A{choice([" titillating", " terrible", " good", "n underwhelming", " sketchy"])} place to go. ' \
                      f'{choice(["Aria", "I", "The dogs", "The pope", "Hemant Mehta", "Dethklok"])} got ' \
                      f'{choice(["diarrhea", "mugged", "a brand new car", "a potato", "an STD", "tinnitus"])}.'
        restaurant = RestaurantRecord(name=name,
                                      date_added=get_random_datetime(),
                                      description=description,
                                      avoid=choice([True, False])
                                      )

        restaurants.append(restaurant)

        # Add tags to restaurant object
        tmp = food_tags.copy()
        for _ in range(randint(1, len(food_tags))):
            restaurant.tags.append(tmp.pop(randint(0, len(tmp) - 1)))

        # Create RestaurantVisit objects with random date and store in list
        for _ in range(randint(11, 15)):
            visit = RestaurantVisit(date=get_random_datetime(),
                                    visit_rating=choice(
                                        ['Loved it!', 'Liked it', 'It was okay', 'Did not like it']),
                                    price_rating=choice(['$', '$$', '$$$', '$$$$']),
                                    comments=f'Ate at {name}.',
                                    record=restaurant,
                                    meal=choice([None,
                                                 'breakfast',
                                                 'lunch',
                                                 'dinner',
                                                 'snack',
                                                 'brunch',
                                                 'drinks', ]
                                                )
                                    )
            visits.append(visit)

        # Create RestaurantNote objects and store in list
        for _ in range(randint(11, 15)):
            date = get_random_datetime()
            note = RestaurantNote(date_added=date,
                                  last_edited=date,
                                  note=f'A note for {name} on {date.strftime("%A, %B %d")}.',
                                  record=restaurant,
                                  )
            notes.append(note)

    # Add all Restaurant objects to database
    db.session.add_all(restaurants)
    db.session.commit()


if __name__ == '__main__':
    fill_restaurant_tables(True, True)
