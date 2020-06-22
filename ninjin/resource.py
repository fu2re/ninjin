# -*- coding: utf-8 -*-
"""Resource classes which can be registered at pool."""
import operator
import re
from typing import Iterable

from aio_pika import IncomingMessage
from gino import NoResultFound

from ninjin.decorator import (
    actor,
    lazy,
)
from ninjin.exceptions import (
    UnknownHandler,
    ValidationError,
)
from ninjin.filtering import (
    ALL,
    BasicFiltering,
)
from ninjin.logger import logger
from ninjin.ordering import ModelResourceOrdering
from ninjin.pagination import ModelResourcePagination
from ninjin.schema import IdSchema


class Resource:
    """Resource helper class providing an easy implementation of custom handlers."""

    pool = None
    consumer_key = None
    serializer_class = None
    deserializer_class = None
    actors = {}
    periodic_tasks = {}

    def __init__(self, deserialized_data, message: IncomingMessage):
        """
        Resource initialization.

        Object is created per each request.

        :param deserialized_data: data dictionary
        :param message: RMQ message
        """
        self.deserialized_data = deserialized_data
        self.message = message
        self.raw = deserialized_data.get('payload', {})
        self.payload = None

    @classmethod
    def resource_name(cls):
        """
        Resource name.

        :return: resource name
        """
        return re.sub('(resource)$', '', cls.__name__.lower())

    async def filter(self, *args, **kwargs):  # noqa: A003
        """
        Filter payload by payload parameters.

        :return: None
        """
        raise NotImplementedError()

    async def paginate(self, *args, **kwargs):
        """
        Paginate payload by payload parameters.

        :return: None
        """
        raise NotImplementedError()

    async def order(self, *args, **kwargs):
        """
        Order payload by payload parameters.

        :return: None
        """
        raise NotImplementedError()

    def serialize(self, data: [dict, Iterable]) -> dict:
        """
        Validate and return response data.

        Fires before data publishing back to response queue.

        :param data:
        :return:
        """
        if not self.serializer_class:
            return data
        return self.serializer_class(many=isinstance(data, list)).dump(data)

    def deserialize(self, data: dict) -> dict:
        """
        Validate and return current data.

        Fires before resource is created. Many is not allowed at the moment.

        :param data: data dictionary
        :return: validated data dictionary
        """
        if not self.deserializer_class:
            return data
        return self.deserializer_class().load(data)

    def validate(self, data: dict):
        """
        Validate incoming data.

        Raises an exception an case if any errors.

        :param data: data dictionary
        :return: None
        """
        if self.serializer_class:
            errors = self.serializer_class.validate(data)
            if errors:
                raise ValidationError('Deserialization Error: {0}'.format(errors))

    async def dispatch(self):
        """
        Find a proper handler method and call it.

        :return: handler result data
        """
        handler_name = self.deserialized_data['handler']
        handler = self.actors.get(handler_name, self.periodic_tasks.get(handler_name))
        if not handler:
            raise UnknownHandler('Handler with name `{0}` is not registered at {1}'.format(
                handler_name,
                self.__class__.__name__,
            ))
        self.serializer_class = getattr(handler, 'serializer_class', self.serializer_class)
        self.deserializer_class = getattr(handler, 'deserializer_class', self.deserializer_class)
        self.payload = self.deserialize(self.raw)
        return await handler.func(self)


class ModelResource(Resource):
    """Resource helper class providing an easy implementation of CRUD handlers."""

    model = None
    serializer_class = IdSchema
    deserializer_class = serializer_class
    filtering_class = BasicFiltering
    pagination_class = ModelResourcePagination
    ordering_class = ModelResourceOrdering
    allowed_filters = {
        'id': ALL,
    }
    allowed_ordering = None
    items_per_page = 100
    max_items_per_page = 1000

    def __init__(self, deserialized_data, message: IncomingMessage):
        """
        Object is created per each request.

        :param deserialized_data: data dictionary
        :param message: RMQ message
        """
        super().__init__(deserialized_data, message)
        self.filtering = self.payload

        self.filtering = self.filtering_class(
            self.model,
            filtering=deserialized_data.get('filtering'),
            allowed_filters=self.allowed_filters,
        )
        self.ordering = self.ordering_class(
            ordering=deserialized_data.get('ordering'),
            allowed_ordering=self.allowed_ordering,
        )
        self.pagination = self.pagination_class(
            deserialized_data.get('pagination'),
            items_per_page=self.items_per_page,
            max_items_per_page=self.max_items_per_page,
        )

    @classmethod
    def resource_name(cls):
        """
        Resource name.

        :return: resource name
        """
        return re.sub('(resource)$', '', getattr(cls, 'model', cls).__name__.lower())

    @lazy
    def _db(self):
        return self.model.__metadata__

    @lazy
    def _table(self):
        return self._db.tables[self.model.__tablename__]

    @lazy
    def _primary_key(self):
        return self._table.primary_key.columns.keys()[0]

    def filter(self, query):  # noqa: A003
        """
        Filter payload by payload parameters.

        :param query: SQL Alchemy core query.
        :return: SQL Alchemy core query.
        """
        return self.filtering.filter(query)

    def paginate(self, query):
        """
        Paginate payload by payload parameters.

        :param query: SQL Alchemy core query.
        :return: SQL Alchemy core query.
        """
        return self.pagination.paginate(query)

    def order(self, query):
        """
        Order payload by payload parameters.

        :param query: SQL Alchemy core query.
        :return: SQL Alchemy core query.
        """
        return self.ordering.order_by(query)

    @lazy
    def query(self):
        """
        Query.

        To provide an easy inheritance.

        :return: SQL Alchemy core query.
        """
        return self.filter(self.model.query)

    @lazy
    def ident(self):
        """
        Object identifier retrieved from payload.

        :return: object primary key value
        """
        try:
            return self.payload.pop(self._primary_key)
        except KeyError:
            return self.filtering.filtering.get(self._primary_key)

    async def exists(self, expr):
        """
        Check if object exists.

        :param expr: SQL Alchemy core expression
        :return: True if an object exists
        """
        return await self._db.scalar(self._db.exists().where(
            expr,
        ).select())

    async def perform_create(self):
        """
        Create an object from payload.

        :return: Resource model object
        """
        expr = operator.eq(getattr(self.model, self._primary_key), self.ident)
        if not await self.exists(expr):
            return await self.model.create(
                **{self._primary_key: self.ident},
                **self.payload,
            )
        else:
            logger.debug('Object {0} with ident = {1} already exists'.format(
                self.model.__name__,
                self.ident,
            ))

    @actor(never_reply=True)
    async def create(self):
        """
        Create an object from payload handler.

        :return: Resource model object
        """
        return await self.perform_create()

    async def perform_update(self):
        """
        Update an object from payload.

        Bulk update is not supported.

        :return: Resource model object
        """
        obj = await self.perform_get()
        if obj:
            await obj.update(**self.payload).apply()
        return obj

    @actor(never_reply=True)
    async def update(self):
        """
        Update an object from payload handler.

        :return: Resource model object
        """
        return await self.perform_update()

    async def perform_delete(self):
        """
        Delete an object.

        :return: None
        """
        obj = await self.perform_get()
        if obj:
            await obj.delete()

    @actor(never_reply=True)
    async def delete(self):
        """
        Object deletion handler.

        :return: None
        """
        await self.perform_delete()

    async def perform_get(self):
        """
        Retrieve an object.

        :return: Resource model object
        """
        try:
            expr = operator.eq(getattr(self.model, self._primary_key), self.ident)
            return await self.query.where(expr).gino.one()
        except NoResultFound:
            return None

    @actor()
    async def get(self):
        """
        Retrieve handler.

        :return: Resource model object
        """
        return await self.perform_get()

    async def perform_get_list(self):
        """
        Get object list.

        :return: object list
        """
        query = self.order(self.query)
        query = self.paginate(query)
        return await query.gino.all()

    @actor()
    async def get_list(self):
        """
        Get list handler.

        :return: object list
        """
        return await self.perform_get_list()
