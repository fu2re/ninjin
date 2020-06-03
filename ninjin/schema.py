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
    pagination = fields.Raw(required=False)

    class Meta:
        unknown = EXCLUDE


class IdSchema(Schema):
    id = fields.UUID(required=False)

    class Meta:
        unknown = EXCLUDE
