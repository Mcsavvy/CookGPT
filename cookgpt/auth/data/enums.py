from enum import Enum


class UserType(Enum):
    """different user types"""

    ADMIN = "admin"
    PATIENT = "patient"
    MEDIC = "medic"
