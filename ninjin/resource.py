import operator
from typing import Iterable

from aio_pika import IncomingMessage
from gino import NoResultFound

from ninjin.decorator import actor
from ninjin.exceptions import (
    UnknownHandler,
    ValidationError
)
from ninjin.filtering import (
    ALL,
    BasicFiltering
)
from ninjin.lazy import lazy
from ninjin.logger import logger
from ninjin.ordering import BasicOrdering
from ninjin.pagination import BasicPagination
from ninjin.schema import IdSchema


class Resource:
    consumer_key = None
    serializer_class = None
    deserializer_class = None

    def __init__(self, deserialized_data, message: IncomingMessage):
        self.handler_name = deserialized_data['handler']
        self.payload = self.deserialize(deserialized_data.get('payload', {}))
        self.message = message

    @lazy
    def handler(self):
        try:
            handler = getattr(self, self.handler_name)
        except (AttributeError, TypeError):
            raise UnknownHandler('Handler with name `{}` is not registered at {}'.format(
                self.handler,
                self.__class__.__name__
            ))
        return handler

    async def filter(self, *args, **kwargs):
        raise NotImplementedError()

    async def paginate(self, *args, **kwargs):
        raise NotImplementedError()

    async def order(self, *args, **kwargs):
        raise NotImplementedError()

    def serialize(self, data: [dict, Iterable]) -> dict:
        if not self.serializer_class:
            return data
        return self.serializer_class(many=isinstance(data, list)).dump(data)

    def deserialize(self, data: dict) -> dict:
        """
        many is not allowed at the moment
        :param data:
        :return:
        """
        if not self.deserializer_class:
            return data
        return self.deserializer_class().load(data)

    def validate(self, data: dict):
        """
        Not necessary as soon as it validated during deserialization already
        :param data:
        :return:
        """
        if self.serializer_class:
            errors = self.serializer_class.validate(data)
            if errors:
                raise ValidationError('Deserialization Error: {}'.format(errors))

    async def dispatch(self):
        return await self.handler()


class ModelResource(Resource):
    model = None
    serializer_class = IdSchema
    deserializer_class = serializer_class
    filtering_class = BasicFiltering
    pagination_class = BasicPagination
    ordering_class = BasicOrdering
    allowed_filters = {
        'id': ALL
    }
    allowed_ordering = None
    items_per_page = 100
    max_items_per_page = 1000

    def __init__(self, deserialized_data, message: IncomingMessage):
        super().__init__(deserialized_data, message)
        self.filtering = self.payload

        self.filtering = self.filtering_class(
            self.model,
            filtering=deserialized_data.get('filtering'),
            allowed_filters=self.allowed_filters
        )
        self.ordering = self.ordering_class(
            ordering=deserialized_data.get('ordering'),
            allowed_ordering=self.allowed_ordering
        )
        self.pagination = self.pagination_class(
            deserialized_data.get('pagination'),
            items_per_page=self.items_per_page,
            max_items_per_page=self.max_items_per_page
        )

    async def dispatch(self):
        return await self.handler()

    @lazy
    def _db(self):
        return self.model.__metadata__

    @lazy
    def _table(self):
        return self._db.tables[self.model.__tablename__]

    @lazy
    def _primary_key(self):
        return self._table.primary_key.columns.keys()[0]

    def filter(self, query):
        return self.filtering.filter(query)

    def paginate(self, query):
        return self.pagination.paginate(query)

    def order(self, query):
        return self.ordering.order_by(query)

    @lazy
    def query(self):
        """
        To provide an easy inheritance
        :return:
        """
        return self.filter(self.model.query)

    @lazy
    def ident(self):
        try:
            return self.payload.pop(self._primary_key)
        except KeyError:
            return self.filtering.filtering.get(self._primary_key)

    async def exists(self, expr):
        return await self._db.scalar(self._db.exists().where(
            expr
        ).select())

    async def perform_create(self):
        expr = operator.eq(getattr(self.model, self._primary_key), self.ident)
        if not await self.exists(expr):
            return await self.model.create(
                **{self._primary_key: self.ident},
                **self.payload,
            )
        else:
            logger.debug('Object {} with ident = {} already exists'.format(
                self.model.__name__,
                self.ident
            ))

    @actor(never_reply=True)
    async def create(self):
        return await self.perform_create()

    async def perform_update(self):
        """
        bulk update is not supported
        :return:
        """
        obj = await self.perform_get()
        if obj:
            await obj.update(**self.payload).apply()
        return obj

    @actor(never_reply=True)
    async def update(self):
        return await self.perform_update()

    async def perform_delete(self):
        obj = await self.perform_get()
        if obj:
            await obj.delete()
        return obj

    @actor(never_reply=True)
    async def delete(self):
        return await self.perform_delete()

    async def perform_get(self):
        try:
            expr = operator.eq(getattr(self.model, self._primary_key), self.ident)
            return await self.query.where(expr).gino.one()
        except NoResultFound:
            return None

    @actor()
    async def get(self):
        return await self.perform_get()

    async def perform_get_list(self):
        query = self.order(self.query)
        query = self.paginate(query)
        return await query.gino.all()

    @actor()
    async def get_list(self):
        return await self.perform_get_list()
