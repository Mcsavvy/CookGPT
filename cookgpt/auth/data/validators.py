"""schema validators"""

from apiflask import validators as v
from marshmallow.exceptions import SCHEMA, ValidationError

from .enums import BloodType as BloodTypeEnum
from .enums import GenderType as GenderTypeEnum


def useValidator(validator, field_name: str = SCHEMA, *args, **kwargs):
    """Allows you use a builtin validator and pass in `field_name`"""

    validate = validator(*args, **kwargs)

    def helper(value):
        try:
            return validate(value)
        except ValidationError as err:
            raise ValidationError(
                err.messages, field_name=field_name
            ) from None

    return helper


class Name(v.Validator):
    """first name validator"""

    LENGTH_ERR = ""
    CHARSET_ERR = ""

    def __init__(self, field_name="first_name"):
        self.field_name = field_name

    def __call__(self, value):
        useValidator(
            v.Length,
            min=2,
            max=25,
            error=self.LENGTH_ERR,
            field_name=self.field_name,
        )(value)
        useValidator(
            v.Regexp, self.field_name, r"^[a-zA-Z]+$", error=self.CHARSET_ERR
        )(value)
        return value


class FirstName(Name):
    """first name validator"""

    LENGTH_ERR = "First Name must be between 2 and 25 characters long"
    CHARSET_ERR = "First Name can only contain letters"

    def __init__(self, field_name="first_name"):
        super().__init__(field_name)


class LastName(Name):
    """last name validator"""

    LENGTH_ERR = "Last Name must be between 2 and 25 characters long"
    CHARSET_ERR = "Last Name can only contain letters"

    def __init__(self, field_name="last_name"):
        super().__init__(field_name)


class Email(v.Validator):
    """email validator"""

    FORMAT_ERR = "Email is not a valid email address"

    def __init__(self, field_name="email"):
        self.field_name = field_name

    def __call__(self, value):
        useValidator(
            v.Email, error=self.FORMAT_ERR, field_name=self.field_name
        )(value)
        return value


class Username(v.Validator):
    """username validator"""

    LENGTH_ERR = "Username must be between 5 and 45 characters long"
    CHARSET_ERR = (
        "Username can only contain "
        "letters, numbers, underscores and hyphens"
    )
    LETTER_ERR = "Username must contain at least one letter"
    START_ERR = "Username must start with a letter"

    def __init__(self, field_name="username"):
        self.field_name = field_name

    def __call__(self, value):
        import string

        useValidator(
            v.Length,
            min=2,
            max=45,
            error=self.LENGTH_ERR,
            field_name=self.field_name,
        )(value)
        useValidator(
            v.Regexp,
            self.field_name,
            r"^[a-zA-Z0-9_-]+$",
            error=self.CHARSET_ERR,
        )(value)
        if not any(char in string.ascii_letters for char in value):
            raise ValidationError(
                [self.LETTER_ERR], field_name=self.field_name
            )
        if value[0] not in string.ascii_letters:
            raise ValidationError([self.START_ERR], field_name=self.field_name)
        return value


class Password(v.Validator):
    """password validator"""

    UPPERCASE_ERR = "Password should contain an uppercase character"
    LOWERCASE_ERR = "Password should contain a lowercase character"
    PUNCTUATION_ERR = "Password should contain a special character"
    DIGIT_ERR = "Password should contain a digit"
    LENGTH_ERR = "Password must be at least 8 characters long"

    def __init__(self, min_length=8, field_name="password"):
        self.min_length = min_length
        self.field_name = field_name

    def __call__(self, value):
        import string

        errors = []
        checks = 0
        useValidator(
            v.Length, min=8, error=self.LENGTH_ERR, field_name=self.field_name
        )(value)
        if any(char in string.ascii_lowercase for char in value):
            checks += 1
        else:
            errors.append(self.LOWERCASE_ERR)
        if any(char in string.ascii_uppercase for char in value):
            checks += 1
        else:
            errors.append(self.UPPERCASE_ERR)
        if any(char in string.digits for char in value):
            checks += 1
        else:
            errors.append(self.DIGIT_ERR)
        if any(char in string.punctuation for char in value):
            checks += 1
        else:
            errors.append(self.PUNCTUATION_ERR)
        if checks > 2:
            errors.clear()
        if len(errors) > 0:
            raise ValidationError(errors, field_name=self.field_name)
        return value


class Login(v.Validator):
    """login validator"""

    FORMAT_ERR = "Login must be a valid email address or username"

    def __init__(self, field_name="login"):
        self.field_name = field_name

    def __call__(self, value):
        try:
            Username()(value)
            return value
        except ValidationError:
            try:
                Email()(value)
                return value
            except ValidationError:
                raise ValidationError(
                    self.FORMAT_ERR, field_name=self.field_name
                )


class Height(v.Validator):  # pragma: no cover
    """height validator"""

    def __init__(self, field_name="height"):
        self.field_name = field_name

    def __call__(self, value):
        import re

        # format: 5ft6in
        feet_regex = re.compile(r"^(?P<ft>\d+)ft(?:(?P<in>\d+)in)?$")
        metric_regex = re.compile(r"^(?P<m>\d+(?:\.\d+)?)m?$")
        feet_match = feet_regex.match(value)
        metric_match = metric_regex.match(value)
        if feet_match:
            feet, inches = feet_match.groups()
            inches = int(inches or 0)
            if inches > 11:
                raise ValidationError("inches must be less than 12")
            feet = int(feet)
            height_in_metres = (feet * 12 + inches) * 0.0254
        elif metric_match:
            height_in_metres = float(metric_match.group("m"))
        else:
            raise ValidationError("invalid height")
        if height_in_metres < 0.0 or height_in_metres > 3:
            raise ValidationError("height out of range")
        return height_in_metres


class Weight(v.Validator):  # pragma: no cover
    """weight validator"""

    def __init__(self, field_name="weight"):
        self.field_name = field_name

    def __call__(self, value):
        import re

        # format: 80kg, 180lb
        kg_regex = re.compile(r"^(?P<kg>\d+(?:\.\d+)?)(?:kg)?$")
        lb_regex = re.compile(r"^(?P<lb>\d+(?:\.\d+)?)lb$")
        lb_match = lb_regex.match(value)
        kg_match = kg_regex.match(value)
        if kg_match:
            weight_in_kg = float(kg_match.group("kg"))
        elif lb_match:
            weight_in_kg = float(lb_match.group("lb")) * 0.453592
        else:
            raise ValidationError("invalid weight")
        if weight_in_kg < 0.0 or weight_in_kg > 635:
            raise ValidationError("weight out of range")
        return weight_in_kg


class DOB(v.Validator):  # pragma: no cover
    """date of birth validator"""

    def __init__(self, field_name="dob"):
        self.field_name = field_name

    def __call__(self, dob):
        from datetime import date, datetime, timedelta

        today = datetime.combine(date.today(), datetime.min.time())
        if dob > today:
            raise ValidationError("date of birth cannot be in the future")
        if dob < today - timedelta(days=365 * 120):
            raise ValidationError(
                "date of birth cannot be more than 120 years ago"
            )
        return dob.date()


class BloodType(v.Validator):  # pragma: no cover
    """blood type validator"""

    def __init__(self, field_name="blood_type"):
        self.field_name = field_name

    def __call__(self, value):
        if len(value) < 2 or len(value) > 3:
            raise ValidationError(
                f"{self.field_name} must be between 2 and 3 characters"
            )
        try:
            return BloodTypeEnum(value.upper())
        except ValueError:
            raise ValidationError(f"invalid {self.field_name}")


class Gender(v.Validator):  # pragma: no cover
    """gender validator"""

    def __init__(self, field_name="gender"):
        self.field_name = field_name

    def __call__(self, value):
        gender_map = {
            "m": "male",
            "f": "female",
            "n": "non-binary",
            "o": "non-binary",
            "non_binary": "non-binary",
            "nonbinary": "non-binary",
            "other": "non-binary",
        }
        value = value.lower()
        if value in gender_map:
            value = gender_map[value]
        try:
            return GenderTypeEnum(value.upper())
        except ValueError:
            raise ValidationError(f"invalid {self.field_name}")
