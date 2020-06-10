import typing
from marshmallow import (
    EXCLUDE,
    Schema,
    fields
)


class PaginationSchema(Schema):
    page = fields.Integer(required=True, default=0)
    size = fields.Integer(required=False, default=100)


class PayloadSchema(Schema):
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

    class Meta:
        unknown = EXCLUDE

    def loads(self, json_data: bytes, *args, **kwargs):
        return super(PayloadSchema, self).loads(
            json_data=json_data.decode('utf-8'),
            *args, **kwargs
        )

    def dumps(self, obj: typing.Any, *args, many: bool = None, **kwargs):
        return super(PayloadSchema, self).dumps(
            obj=obj,
            *args, **kwargs).encode('utf-8')


class IdSchema(Schema):
    id = fields.UUID(required=False)

    class Meta:
        unknown = EXCLUDE
