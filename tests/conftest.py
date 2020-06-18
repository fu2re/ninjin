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
from ninjin.pool import Pool
from tests.models import PG_URL, POOL_ARGS, UserResource, db


ECHO = False


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
async def broker(event_loop: asyncio.AbstractEventLoop):
    connection = await aio_pika.connect_robust(
        host=os.getenv('BROKER_HOST', 'localhost'),
        port=int(os.getenv('BROKER_PORT', 5672)),
        login=os.getenv('BROKER_LOGIN', 'guest'),
        password=os.getenv('BROKER_PASSWORD', 'guest'),
        loop=event_loop
    )
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        name=os.getenv('BROKER_EXCHANGE_NAME', 'adapter'),
        type=os.getenv('BROKER_EXCHANGE_TYPE', 'topic'),
        durable=os.getenv('BROKER_EXCHANGE_DURABLE', True),
        auto_delete=os.getenv('BROKER_EXCHANGE_AUTO_DELETE', False)
    )
    # Before tests
    await yield_((connection, exchange, channel))

    # After tests
    try:
        await exchange.delete()
        await connection.close()
    except Exception:
        pass



@pytest.fixture
@async_generator
async def bind(sa_engine):
    async with db.with_bind(PG_URL, echo=ECHO) as e:
        await yield_(e)
    sa_engine.execute("DELETE FROM users")


@pytest.fixture()
@async_generator
async def pool():
    pool = Pool(
        **POOL_ARGS
    )
    await pool.connect()
    await yield_(pool)
    await pool.close()
