# -*- coding: utf-8 -*-
"""Marshmallow schemas to validate payloads."""
import typing

import simplejson as simplejson
from marshmallow import (
    EXCLUDE,
    Schema,
    fields,
)


class PaginationSchema(Schema):
    """Pagination schema."""

    page = fields.Integer(required=True, default=0)
    size = fields.Integer(required=False, default=100)


class PayloadSchema(Schema):
    """Payload schema."""

    resource = fields.String(required=False, allow_none=True)
    handler = fields.String(required=True)
    payload = fields.Raw(required=False)

    filtering = fields.Raw(required=False)
    ordering = fields.String(required=False)
    pagination = fields.Raw(required=False, allow_none=True)

    # scheduler only fields
    forward = fields.String(required=False, allow_none=True)
    period = fields.Integer(required=False, allow_none=True)
    repeat = fields.Boolean(required=False, allow_none=True)

    class Meta:  # noqa: D106
        unknown = EXCLUDE
        json_module = simplejson

    def loads(self, json_data: bytes, *args, **kwargs):
        """
        Load data from json.

        :param json_data: incoming message data
        :param args:
        :param kwargs:
        :return: validated dictionary
        """
        return super(PayloadSchema, self).loads(
            json_data=json_data.decode('utf-8'),
            *args, **kwargs,
        )

    def dumps(self, obj: typing.Any, *args, many: bool = None, **kwargs):
        """
        Dump data to json.

        :param obj: dictionary or object
        :param args:
        :param many: true if multiple multiple objects presented
        :param kwargs:
        :return: json
        """
        return super(PayloadSchema, self).dumps(
            obj=obj,
            *args, **kwargs).encode('utf-8')


class IdSchema(Schema):
    """Simplest possible resource schema."""

    id = fields.UUID(required=False)  # noqa: A003

    class Meta:  # noqa: D106
        unknown = EXCLUDE
