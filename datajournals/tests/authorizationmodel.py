from datajournals import db
from datajournals.authorization import init_authorization_tables
from datajournals.authorization.init_db import init_default_roles
from datajournals.models import Role, User


def fill_authorization_tables(init: bool = False, set_default_tags: bool = False):

    # Reinitialize tables
    if init:
        init_authorization_tables()
    if set_default_tags:
        init_default_roles()

    # Create roles objects. Check if any roles already exist in database.
    roles = Role.query.all()
    if not roles:
        admin_role = Role(rolename='admin')
        editor_role = Role(rolename='editor')
        visitor_role = Role(rolename='visitor')
        roles = [admin_role, editor_role, visitor_role]
    else:
        admin_role = Role.query.filter_by(rolename='admin').first()
        editor_role = Role.query.filter_by(rolename='editor').first()
        visitor_role = Role.query.filter_by(rolename='visitor').first()

    # Create users details
    users = {
        ('adminuser', 'admin@example.com', 'adminpass', admin_role),
        ('edituser', 'editor@example.com', 'editpass', editor_role),
        ('visituser', 'visitor@example.com', 'visitpass', visitor_role),
    }

    # Create User objects and add to database
    user_objects = []
    for user in users:
        user_obj = User()
        user_obj.username = user[0]
        user_obj.email = user[1]
        user_obj.password = user[2]
        user_obj.role = user[3]
        user_objects.append(user_obj)

    db.session.add_all(user_objects)
    db.session.commit()


if __name__ == '__main__':
    fill_authorization_tables(True, True)
