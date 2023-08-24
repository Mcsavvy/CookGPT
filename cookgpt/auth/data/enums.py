from enum import Enum


class BloodType(Enum):
    """different blood types"""

    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"


class GenderType(Enum):
    """different genders"""

    MALE = "MALE"
    FEMALE = "FEMALE"
    NON_BINARY = "NON-BINARY"


class UserType(Enum):
    """different user types"""

    ADMIN = "admin"
    PATIENT = "patient"
    MEDIC = "medic"
