# -*- coding: utf-8 -*-
"""Exceptions."""


class ImproperlyConfigured(Exception):
    """Configuration error."""


class UnknownConsumer(Exception):
    """Resource does not exist."""


class UnknownHandler(Exception):
    """Handler does not exist."""


class IncorrectMessage(Exception):
    """RMQ Message is invalid."""


class ValidationError(Exception):
    """Payload is invalid or marshmallow schema is invalid."""
