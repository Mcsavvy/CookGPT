from contextlib import contextmanager

from faker import Faker

fake = Faker()

_Missing = object()


@contextmanager
def update_config(config, **configs):
    """update the app's config temporarily"""
    undefined = object()
    old_config = {}
    for k, v in configs.items():
        old_config[k] = config.get(k, undefined)
        config[k] = v
    try:
        yield
    finally:
        for k, v in old_config.items():
            if v is undefined:
                del config[k]
            else:
                config[k] = v


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
    return fake.password()


def random_user(
    first_name=_Missing,
    last_name=_Missing,
    email=_Missing,
    password=_Missing,
    username=_Missing,
    save=True,
):
    """create a random user"""
    from cookgpt.user.models import User

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
    return User.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        username=username,
        commit=save,
    )


def extract_access_token(response):
    """extract access token from response"""
    return response.headers["Set-Cookie"].split(";")[0].split("=")[1]
