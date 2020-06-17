import asyncio
import datetime
import os
import uuid

import aio_pika
import gino
import pytest
import sqlalchemy
from async_generator import (
    async_generator,
    yield_,
)
from gino import Gino
from sqlalchemy.dialects.postgresql import UUID

from tests.models import PG_URL

db = Gino()


@pytest.fixture(scope="module")
def sa_engine():
    rv = sqlalchemy.create_engine(PG_URL, echo=False)
    db.create_all(rv)
    yield rv
    db.drop_all(rv)
    rv.dispose()


@pytest.fixture
@async_generator
async def engine(sa_engine):
    e = await gino.create_engine(PG_URL, echo=False)
    await yield_(e)
    await e.close()
    sa_engine.execute("DELETE FROM users")


@pytest.fixture
@async_generator
async def broker():
    loop = asyncio.get_event_loop()
    connection = await aio_pika.connect_robust(
        host=os.getenv('BROKER_HOST', 'rabbitmq'),
        port=int(os.getenv('BROKER_PORT', 5672)),
        login=os.getenv('BROKER_LOGIN', 'guest'),
        password=os.getenv('BROKER_PASSWORD', 'guest'),
        loop=loop
    )
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        name=os.getenv('BROKER_EXCHANGE_NAME'),
        type=os.getenv('BROKER_EXCHANGE_TYPE', 'topic'),
        durable=os.getenv('BROKER_EXCHANGE_DURABLE', False),
        auto_delete=os.getenv('BROKER_EXCHANGE_AUTO_DELETE', True)
    )
    return connection, exchange, channel
