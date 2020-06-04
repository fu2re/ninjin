import asyncio
import inspect
import json
import re
import uuid
from collections import UserDict

from aio_pika import (
    DeliveryMode,
    IncomingMessage,
    Message
)
from dynaconf import settings

from ninjin.exceptions import (
    ImproperlyConfigured,
    IncorrectMessage,
    UnknownConsumer
)
from ninjin.lazy import lazy
from ninjin.logger import logger
from ninjin.schema import PayloadSchema
from ninjin.utils import init_aio_pika

schema = PayloadSchema()


class Consumer(UserDict):
    """
    Single queue - single customer
    Multiple models is allowed at the payload
    Each model has multiple handlers inside
    """
    def __init__(self, queue_getter):
        super(Consumer, self).__init__()
        self.queue_getter = queue_getter

    async def consume(self):
        async def extractor(message: IncomingMessage):
            async with message.process(requeue=False):
                msg = message.body.decode('utf-8')
                logger.debug('Received message: {}'.format(msg))
                deserialized_data = schema.loads(msg)
                resource_name = deserialized_data.get('resource')
                try:
                    resource = self[resource_name]
                except KeyError:
                    error_msg = 'Resource {} does not registered'.format(resource_name)
                    logger.debug(error_msg)
                    raise UnknownConsumer(error_msg)

                await resource(deserialized_data, message).dispatch()

        queue = await self.queue_getter()
        await queue.consume(callback=extractor)


class Pool(UserDict):
    connection = None
    exchange = None
    channel = None
    main_queue = None
    callback_queue = None
    queues = {}
    futures = {}

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Pool, cls).__new__(cls)
        return cls.instance

    def __init__(self, *args, **kwargs):
        super(Pool, self).__init__()

    @lazy
    def service_name(self):
        """
        actually service name can be found by the\
        >>> os.path.split(os.path.dirname(inspect.stack()[1][1]))[-1]
        :return:
        """
        # TODO
        return settings.SERVICE_KEY

    @lazy
    def rpc_name(self):
        return '{}.RPC'.format(self.service_name)

    async def establish(self):
        connection, exchange, channel = await init_aio_pika()
        self.connection = connection
        self.exchange = exchange
        self.channel = channel
        self.callback_queue = await self.channel.declare_queue(
            name=self.rpc_name,
            durable=True
        )
        await self.callback_queue.bind(exchange)

    def get_queue(self, consumer_key):
        async def inner():
            if not self.channel:
                await self.establish()

            if consumer_key not in self.queues:
                q = await self.channel.declare_queue(
                    name=consumer_key,
                    durable=True
                )
                await q.bind(self.exchange)
                self.queues[consumer_key] = q

            return self.queues[consumer_key]
        return inner

    def connect(self, handler, consumer_key=None, handler_name=None):
        from ninjin.resource import Resource
        if inspect.iscoroutinefunction(handler):
            resource = None
            resource_name = None
            consumer_key = consumer_key or self.service_name
            # TODO

        elif issubclass(handler, Resource):
            resource = handler
            resource_name = re.sub('(resource)$', '', getattr(resource, 'model', resource).__name__.lower())
            consumer_key = consumer_key or resource.consumer_key or self.service_name

        else:
            raise ImproperlyConfigured('Only coroutine or resource can be registered as actor')

        if consumer_key not in self:
            self[consumer_key] = Consumer(queue_getter=self.get_queue(consumer_key))

        if resource_name in self[consumer_key]:
            if resource_name:
                raise ImproperlyConfigured('{} already registered'.format(resource_name))
            # TODO: Find better solution
            resource = type('SimpleResource', (self[consumer_key][resource_name],), {handler_name: handler})

        if not resource:
            resource = type('SimpleResource', (Resource,), {handler_name: handler})

        self[consumer_key][resource_name] = resource

    async def consume(self):
        await asyncio.gather(*[x.consume() for x in self.values()])

    async def publish(
        self,
        payload,
        service_name: str,
        remote_resource=None,
        remote_handler='default',
        correlation_id=None,
        pagination=None,
    ):
        if payload is None:
            raise IncorrectMessage('Cannot publish empty message from')

        msg = schema.dumps({
            'payload': payload,
            'resource': remote_resource,
            'handler': remote_handler,
            'pagination': pagination
        }).encode('utf-8')

        await self.exchange.publish(
            Message(
                body=msg,
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT,
                correlation_id=correlation_id,
                reply_to=self.rpc_name if correlation_id else None,
            ),
            routing_key=service_name
        )

    async def on_rpc_response(self, message: IncomingMessage):
        async with message.process(requeue=False):
            f = self.futures.pop(message.correlation_id)
            f.set_result(json.loads(message.body.decode()))

    async def rpc(
        self,
        payload,
        service_name: str,
        remote_resource=None,
        remote_handler='default',
    ):
        correlation_id = str(uuid.uuid4())
        # TODO loop support?
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self.futures[correlation_id] = future
        await self.callback_queue.consume(self.on_rpc_response)
        await self.publish(
            payload,
            service_name=service_name,
            remote_resource=remote_resource,
            remote_handler=remote_handler,
            correlation_id=correlation_id
        )
        return await future


pool = Pool()
