from contextlib import contextmanager

from faker import Faker

from cookgpt.app import db
from cookgpt.cli import _initdb
from cookgpt.models import Token  # noqa: F401
from cookgpt.models import (Message, MessageMixin, TokenMixin, User, UserInfo,
                            UserInfoMixin)

_initdb(drop=True, create_admin=False)
fake = Faker()

_Missing = object()


@contextmanager
def update_config(config, **configs):
    """update the app's config temporarily"""
    undefined = object()

    old_config = {k: config.get(k, undefined) for k in configs}
    config.update(**configs)
    try:
        yield
    finally:
        for k, v in old_config.items():
            if v is undefined:
                del config[k]
            else:
                config[k] = v


def purge_all():
    # print("purging all data...")
    db.session.rollback()
    for tk in Token.query.all():
        db.session.delete(tk)
    for msg in Message.query.all():
        db.session.delete(msg)
    for info in UserInfo.query.all():
        db.session.delete(info)
    for user in User.query.all():
        db.session.delete(user)
    # print("purged all data.")


def random_first_name():
    """return a random first name"""
    return fake.first_name()


def random_last_name():
    """return a random last name"""
    return fake.last_name()


def random_username():
    """return a random username"""
    username = fake.user_name()
    while len(username) < 5:
        username = fake.user_name()
    return username


def random_email():
    """return a random email"""
    return fake.email()


def random_password():
    """return a random password"""
    import string
    from random import choice

    password = fake.password()
    if not any(c in string.digits for c in password):
        password += choice(string.digits)
    if not any(c in string.punctuation for c in password):
        password += choice(string.punctuation)
    return password


def random_dob():
    """return a random date of birth"""
    return fake.date_of_birth(minimum_age=18, maximum_age=100).isoformat()


def random_blood_group():
    """return a random blood group"""
    from random import choice

    return choice(("A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"))


def random_gender():
    """ "return a random gender"""
    from random import choice

    return choice(("m", "f", "n"))


def random_height():
    """return a random height"""
    from random import randint

    return f"{randint(150, 200)}cm"


def random_weight():
    """return a random weight"""
    from random import randint

    return f"{randint(50, 100)}kg"


def random_user(
    first_name=_Missing,
    last_name=_Missing,
    email=_Missing,
    password=_Missing,
    username=_Missing,
    save=True,
    **info,
):
    """create a random user"""
    if first_name is _Missing:
        first_name = random_first_name()
    if last_name is _Missing:
        last_name = random_last_name()
    if email is _Missing:
        email = random_email()
    if password is _Missing:
        password = random_password()
    if username is _Missing:
        username = random_username()
    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        username=username,
    )
    if save:
        user.save()
        _ = info and user.update_info(**info)
    return user


from .test_models import TestMessage  # noqa: F401,E402
from .test_models import TestBaseModel, TestToken, TestUser, TestUserInfo
