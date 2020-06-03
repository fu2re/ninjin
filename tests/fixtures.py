
import datetime
import uuid

import gino
import pytest
import sqlalchemy
from async_generator import (
    async_generator,
    yield_
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
