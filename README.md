# Ninjin

<img alt="ninjin" src="https://github.com/fu2re/ninjin/blob/master/doc/ninjin.png?raw=true" height="200" />
<br/>

Ninjin (which means carrot) is library for an easy microservices integration with each other. 

Features:
- Predefined messages protocol
- Easy RMQ transport
- GINO integrated
- CRUD out-of-the-box
- Pagination
- Delayed and periodic tasks
- Auto-generated marshmallow validation schemas for GINO model [TODO]
- Auto-generated documentation [TODO]


Register model and schema

```python
from sqlalchemy.dialects.postgresql import UUID
from marshmallow import Schema, fields
from gino import Gino

db = Gino()

class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(UUID, primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String)
    funds = db.Column(db.Integer)
    orders = db.Column(db.Integer)

class CustomerSchema(Schema):
    id = fields.UUID()
    name = fields.Str()
    funds = fields.Integer()
    orders = fields.Integer()
```

Now register a resource. You can specify filters, ordering, pagination options

```python
from ninjin.resource import ModelResource
from ninjin.filtering import ALL, GREATER_THAN, GREATER_THAN_OR_EQUAL, \
    LESSER_THAN, LESSER_THAN_OR_EQUAL, EXACT

class CustomerResource(ModelResource):
    model = Customer
    serializer_class = CustomerSchema
    deserializer_class = serializer_class
    allowed_ordering = 'orders'
    allowed_filtering = {
        'id': (EXACT,),
        'funds': (ALL,),
        'orders': (GREATER_THAN, GREATER_THAN_OR_EQUAL)
    }
    items_per_page = 100
    max_items_per_page = 1000 
```

Register pool and start liten queues.

```python
from ninjin.pool import Pool

async def main():
    pool = Pool(
        service_name='my_service_name',
    )
    await pool.connect()
    await pool.register(CustomerResource)
    await pool.start()
```

Extra handlers example

```python
from ninjin.decorator import actor

class CustomerResource_(CustomerResource):
    @actor()
    async def echo(self):
        return 'hello'
```

Helpers. All CRUD methods available out of the box. Just pass to the handler variable on oth following values:
get, get_list, create, delete and update. Please note that get and get list should be an RPC request. 

```python
async def get_list():
    result = pool.rpc({
        'resource': 'customer',
        "ordering": "-orders",
        "pagination": {
            "items": 50,
            "page": 1
        },
        "handler": "get_list"
    },
    service_name='my_service_name')
    return result
```
```python
async def get():
    result = pool.rpc({
        'resource': 'customer',
        "filtering": {
            "id": "2e363b49-f713-4fa0-9f0f-7dc699290df4"
        },
        "handler": "get"
    },
    service_name='my_service_name')
    return result

```
```python
async def create():
    result = pool.publish({
        'resource': 'customer',
        "payload": {
            "id": "2e363b49-f713-4fa0-9f0f-7dc699290df4",
            "funds": 100,
            "orders": 100
        },
        "handler": "create"
    },
    service_name='my_service_name')
    return result
```
You can pass an primary key both through the payload or through
filtering option

```python
async def update():
    result = pool.publish({
        'resource': 'customer',
        "payload": {
            "id": "2e363b49-f713-4fa0-9f0f-7dc699290df4",
            "funds": 200,
        },
        "handler": "update"
    },
    service_name='my_service_name')
    return result
```
Perform delete. Also you can use bot filtering and payload

```python
async def delete():
    result = pool.publish({
        'resource': 'customer',
        "filtering": {
            "id": "2e363b49-f713-4fa0-9f0f-7dc699290df4"
        },
        "handler": "delete"
    },
    service_name='my_service_name')
    return result
```