import enum
import os
import random
import string
import uuid
from datetime import datetime

import pytest
from faker import Faker
from gino import Gino
from sqlalchemy.dialects.postgresql import UUID

DB_ARGS = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", 5432),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASS", ""),
    database=os.getenv("DB_NAME", "postgres"),
)
PG_URL = "postgresql://{user}:{password}@{host}:{port}/{database}".format(**DB_ARGS)
fake = Faker()
db = Gino()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        UUID,
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow()
    )
    date_updated = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow(),
        onupdate=datetime.utcnow()
    )
    nickname = db.Column(
        db.Unicode(),
        default=fake.name()
    )
    age = db.Column(
        db.Integer,
        default=18
    )
