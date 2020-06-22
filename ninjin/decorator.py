# -*- coding: utf-8 -*-
"""Decorators."""
import functools
import inspect
import types
from functools import wraps

from ninjin.exceptions import ImproperlyConfigured
from ninjin.logger import logger


def lazy(func):
    """
    Lazy property decorator.

    Object property decorator to avoid multiple calculations of the same data.

    :param fn:
    :return:
    """

    @property
    @wraps(func)
    def _lazyprop(self):
        attr_name = '_lazy_' + func.__name__
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)

    return _lazyprop


def listify(func):
    """
    Listify decorator from generator.

    :param func:
    :return:
    """
    @wraps(func)
    def new_func(*args, **kwargs):
        r = func(*args, **kwargs)
        if r is None:
            return []
        if isinstance(r, types.GeneratorType):
            return list(r)
        return r
    return new_func


def actor(
    reply_to: str = None,
    remote_resource=None,
    remote_handler='default',
    never_reply=False,
    **kwargs  # noqa: C816  # python 3.5 cannot handle comma here
):  # noqa: D401
    """
    Decorator to process messages from RMQ.

    Decorated method will consume a messages from RMQ.

    :param reply_to: Routing key where message should be pushed if reply_to is not received
    :param remote_resource: Reply to that resource
    :param remote_handler: Reply to that handler
    :param never_reply: Never reply even if reply_to is received
    :return:
    """
    def real_wrapper(func):
        if not inspect.iscoroutinefunction(func):
            raise ImproperlyConfigured('{0} is not coroutine'.format(func.__name__))

        @functools.wraps(func)
        async def wrapper(
                resource,
                *args,
                **kwargs) -> None:

            message_asked_for_reply = getattr(resource.message, 'reply_to')
            if reply_to and message_asked_for_reply:
                logger.info('Queue is asked for reply at `{0}`,'
                            ' but reply queue is already defined'.format(func.__name__))

            queue_to_reply = reply_to or message_asked_for_reply

            func_result = await func(resource, *args, **kwargs)
            payload = func_result or {}
            if not queue_to_reply or never_reply:
                return

            pagination = None
            payload = resource.serialize(payload)
            # TODO actually some payloads should not be paginated
            if hasattr(resource, 'pagination'):
                pagination = resource.pagination.result

            await resource.pool.publish(
                payload,
                pagination=pagination,
                service_name=queue_to_reply,
                remote_resource=remote_resource,
                remote_handler=remote_handler,
                correlation_id=getattr(resource.message, 'correlation_id'),
            )

        wrapper.is_actor = True
        wrapper.func = func
        if 'serializer_class' in kwargs:
            wrapper.serializer_class = kwargs['serializer_class']
        if 'deserializer_class' in kwargs:
            wrapper.deserializer_class = kwargs['deserializer_class']

        return wrapper

    return real_wrapper


def periodic_task(run_every: int):  # noqa: D401
    """
    Decorator to run method periodically.

    :param run_every: milliseconds
    :return:
    """
    def real_wrapper(func):
        if not inspect.iscoroutinefunction(func):
            raise ImproperlyConfigured('{0} is not coroutine'.format(func.__name__))

        @functools.wraps(func)
        async def wrapper(
                resource,
                *args,
                **kwargs) -> None:

            await resource.pool.schedule(
                period=run_every,
                payload={},
                remote_resource=resource.__class__.resource_name(),
                remote_handler=func.__name__,
            )
        wrapper.is_periodic_task = True
        wrapper.func = func
        return wrapper

    return real_wrapper
