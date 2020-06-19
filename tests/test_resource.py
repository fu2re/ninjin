import pytest
from tests.models import UserResource

pytestmark = pytest.mark.asyncio


async def test_resource_register(pool):
    registered_resources = pool.queues.resources

    assert registered_resources == {}
    await pool.register(UserResource)
    resource_model_name = UserResource.model.__name__.lower()
    assert registered_resources[resource_model_name]


async def test_resource():
    pass


async def test_resource_actor():
    pass


async def test_model_resource():
    pass


async def test_model_resource_create():
    pass


async def test_model_resource_update():
    pass


async def test_model_resource_delete():
    pass


async def test_model_resource_get():
    pass


async def test_model_resource_getlist():
    pass


async def test_resource_filtration():
    pass


async def test_resource_ordering():
    pass


async def test_resource_pagination():
    pass
