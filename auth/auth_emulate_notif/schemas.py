import random

from faker import Faker
from pydantic import BaseModel, Field

fake = Faker()

def gen_bool() -> bool:
    return bool(random.getrandbits(1))


class UserProfile(BaseModel):
    first_name: str = Field(default_factory=fake.first_name)
    last_name: str = Field(default_factory=fake.last_name)
    user_tz: str = Field(default_factory=fake.timezone)


class UserEmail(BaseModel):
    email: str = Field(default_factory=fake.email)


class UserSettings(BaseModel):
    is_notify: bool = Field(default_factory=gen_bool)
