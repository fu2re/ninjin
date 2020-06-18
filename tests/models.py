import os
import random
import string
import uuid
import simplejson
from datetime import datetime
from marshmallow import fields, Schema
from marshmallow_enum import EnumField
import pytest
from faker import Faker
from gino import Gino
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum

from ninjin.decorator import actor
from ninjin.resource import ModelResource
class_id = None

DB_ARGS = {
    'host': os.getenv("DB_HOST", "localhost"),
    'port': os.getenv("DB_PORT", 5432),
    'user': os.getenv("DB_USER", "postgres"),
    'password': os.getenv("DB_PASS", ""),
    'database': os.getenv("DB_NAME", "postgres"),
}
PG_URL = "postgresql://{user}:{password}@{host}:{port}/{database}".format(**DB_ARGS)

SERVICE_NAME = "test_ninjin"
POOL_ARGS = {
    'service_name': os.getenv("SERVICE_NAME", SERVICE_NAME),
    'host': os.getenv("BROKER_HOST", "localhost"),
    'port': os.getenv("BROKER_PORT", 5672),
    'login': os.getenv("BROKER_LOGIN", "guest"),
    'password': os.getenv("BROKER_PASSWORD", "guest"),
    'exchange_name': os.getenv("BROKER_EXCHANGE_NAME", "adapter"),
    'exchange_type': os.getenv("BROKER_EXCHANGE_TYPE", "topic"),
    'exchange_durable': os.getenv("BROKER_EXCHANGE_DURABLE", True),
    'exchange_auto_delete': os.getenv("BROKER_EXCHANGE_AUTO_DELETE", False),
}

fake = Faker()
db = Gino()


class StatusEnum(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    BANNED = 'banned'
    DELETED = 'deleted'


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
    status = db.Column(
        db.Enum(StatusEnum),
        nullable=False,
        default=StatusEnum.INACTIVE
    )


class UserSchema(Schema):
    id = fields.UUID()
    nickname = fields.Str()
    age = fields.Integer()
    status = EnumField(StatusEnum)
    date_created = fields.DateTime(required=False)
    date_updated = fields.DateTime(required=False)

    class Meta:
        json_module = simplejson


class UserResource(ModelResource):
    model = User
    serializer_class = UserSchema
    deserializer_class = serializer_class
    allowed_ordering = 'date_created'

    @actor()
    async def echo(self):
        return 'hello'



