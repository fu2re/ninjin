import operator
from typing import Iterable

from aio_pika import IncomingMessage

from ninjin.decorator import actor
from ninjin.exceptions import UnknownHandler, ValidationError
from ninjin.filtering import BasicFiltering, ALL
from ninjin.lazy import lazy
from ninjin.logger import logger
from ninjin.ordering import BasicOrdering
from ninjin.pagination import BasicPagination
from ninjin.schema import IdSchema


class Resource:
    consumer_key = None
    serializer_class = IdSchema
    deserializer_class = serializer_class

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
        return self.serializer_class(many=isinstance(data, Iterable)).dump(data)

    def deserialize(self, data: dict) -> dict:
        """
        many is not allowed at the moment
        :param data:
        :return:
        """
        return self.deserializer_class().load(data)

    def validate(self, data: dict):
        """
        Not necessary as soon as it validated during deserialization already
        :param data:
        :return:
        """
        errors = self.serializer_class.validate(data)
        if errors:
            raise ValidationError('Deserialization Error: {}'.format(errors))

    async def dispatch(self):
        return await self.handler()


class ModelResource(Resource):
    model = None
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
        query = self.model.query
        query = self.filter(query)
        query = self.order(query)
        query = self.paginate(query)
        return query.gino

    async def exists(self, ident):
        return await self._db.scalar(self._db.exists().where(
            operator.eq(getattr(self.model, self._primary_key), ident)
        ).select())

    @actor(never_reply=True)
    async def create(self):
        ident = self.payload[self._primary_key]
        if not await self.exists(ident):
            return await self.model.create(**self.payload)
        else:
            logger.debug('Object {} with ident = {} already exists'.format(
                self.model.__name__,
                ident
            ))

    @actor(never_reply=True)
    async def update(self):
        """
        bulk update is not supported
        :return:
        """
        obj = await self.get()
        await obj.update(self.payload).apply()

    @actor(never_reply=True)
    async def delete(self):
        obj = await self.get()
        await obj.delete()

    @actor()
    async def get(self):
        return await self.query.one()

    @actor()
    async def get_list(self):
        return await self.query.all()
