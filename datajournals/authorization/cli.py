import click
from email_validator import validate_email, EmailSyntaxError
from flask.cli import AppGroup
from sqlalchemy.exc import IntegrityError

from datajournals.authorization.init_db import init_default_roles
from datajournals.extensions import db
from datajournals.models.authorization import User, Role

rolenames = [x.rolename for x in Role.query.all()]
if not rolenames:
    init_default_roles()
    rolenames = [x.rolename for x in Role.query.all()]
rolenames = sorted(rolenames)
role_help_prompt = rolenames.copy()
last = role_help_prompt.pop(-1)
role_help_prompt = ', '.join(role_help_prompt) + f', or {last}'


user_cli = AppGroup('user')


@user_cli.command('add')
@click.option('--rolename', '-r',
              default='visitor',
              help=f'The role of the user being added. Can be {role_help_prompt}.',
              show_default=True
              )
@click.option('--username', '-u',
              help='The username of the user being added.',
              prompt='Choose a username'
              )
@click.option('--usermail', '-m',
              help='The email of the user being added.',
              prompt='Enter an email'
              )
@click.option("--password", '-p',
              prompt='Enter a password',
              hide_input=True,
              confirmation_prompt=True
              )
def add(rolename, username, usermail, password):
    messages = []

    if rolename not in rolenames:
        messages.append(f'\"{rolename}\" is not a valid role.')

    try:
        usermail = validate_email(usermail, check_deliverability=False)
        usermail = usermail.normalized
    except EmailSyntaxError as e:
        messages.append(e)

    if messages:
        for message in messages:
            click.echo(f'Error: {message}')
    else:
        try:
            user = User()
            user.username = username
            user.email = usermail
            user.password = password
            user.role = Role.query.filter_by(rolename=rolename).first()
            db.session.add(user)
            db.session.commit()
            click.echo(f'User {username} added.')
        except IntegrityError as e:
            click.echo(e)


@user_cli.command('list')
def list_():
    userprofiles = [(x.username, x.role.rolename, x.email) for x in User.query.all()]
    for username, userrole, useremail in userprofiles:
        click.echo(f'{username}: {useremail}; {userrole}')


@user_cli.command('remove')
@click.argument('name')
def remove(name):
    if name in [x.username for x in User.query.all()]:
        db.session.delete(User.query.filter_by(username=name).first())
        db.session.commit()
    else:
        click.echo('Username not found.')


edit_cli = AppGroup('edit')


@edit_cli.command('email')
@click.option('--username',
              help='The name of the user being edited.',
              prompt='Username'
              )
@click.option('--mail',
              help='The user\'s new email.',
              prompt='Email'
              )
def email(username, mail):
    messages = []

    if username not in [x.username for x in User.query.all()]:
        messages.append('Username not found.')

    try:
        mail = validate_email(mail)
        mail = mail.normalized
    except EmailSyntaxError as e:
        messages.append(e)
    except IntegrityError as e:
        messages.append(e)

    if messages:
        for message in messages:
            click.echo(f'Error: {message}')
    else:
        user = User.query.filter_by(username=username).first()
        user.email = mail
        db.session.add(user)
        db.session.commit()
        click.echo(f'User {username} email updated. New email is {mail}.')


@edit_cli.command('role')
@click.option('--username', '-u',
              help='The name of the user being edited.',
              prompt='Username'
              )
@click.option('--rolename', '-r',
              help=f'The user\'s new role: {role_help_prompt}.',
              prompt=f'Role (one of {role_help_prompt})'
              )
def email(username, rolename):
    messages = []

    if username not in [x.username for x in User.query.all()]:
        messages.append(f'Username \"{username}\" not found.')

    if rolename not in rolenames:
        messages.append(f'\"{rolename}\" is not a valid role.')

    if messages:
        for message in messages:
            click.echo(f'Error: {message}')
    else:
        user = User.query.filter_by(username=username).first()
        user.role = Role.query.filter_by(rolename=rolename).first()
        db.session.add(user)
        db.session.commit()
        click.echo(f'User {username} role updated. New role is {rolename}.')


@edit_cli.command('password')
@click.option('--username', '-u',
              help='The name of the user being edited.',
              prompt='Username'
              )
@click.option("--password", '-p',
              prompt='Enter a password',
              hide_input=True,
              confirmation_prompt=True
              )
def password_(username, password):
    messages = []

    if username not in [x.username for x in User.query.all()]:
        messages.append(f'Username \"{username}\" not found.')

    if messages:
        for message in messages:
            click.echo(f'Error: {message}')
    else:
        user = User.query.filter_by(username=username).first()
        user.password = password
        db.session.add(user)
        db.session.commit()
        click.echo(f'User {username} password updated.')


user_cli.add_command(edit_cli)
