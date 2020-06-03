import functools
import inspect

from ninjin.exceptions import ImproperlyConfigured
from ninjin.logger import logger
from ninjin.pool import pool


def reply(
    reply_to: str,
    remote_resource=None,
    remote_handler='default',
    never_reply=False,
    raw_reply=False
):
    def real_wrapper(func):
        async def wrapper(
                resource,
                *args,
                **kwargs) -> None:
            message_asked_for_reply = getattr(resource.message, 'reply_to')
            if reply_to and message_asked_for_reply:
                logger.info('Queue is asked for reply at `{}`,'
                            ' but reply queue is already defined'.format(func.__name__))

            queue_to_reply = reply_to or message_asked_for_reply
            payload = await func(resource, *args, **kwargs)
            payload = payload or {}
            if not queue_to_reply or never_reply:
                return

            pagination = None
            if not raw_reply:
                payload = resource.serialize(payload)
                if hasattr(resource, 'pagination'):
                    pagination = resource.pagination.result

            await pool.publish(
                payload,
                pagination=pagination,
                service_name=queue_to_reply,
                remote_resource=remote_resource,
                remote_handler=remote_handler,
                correlation_id=getattr(resource.message, 'correlation_id')
            )
        return wrapper
    return real_wrapper


def actor(
    reply_to: str = None,
    remote_resource=None,
    remote_handler='default',
    never_reply=False,
    raw_reply=False
):
    """
    Decorator to process received messages

    :param raw_reply:
    :param reply_to: Routing key where message should be pushed
    :param remote_resource:
    :param remote_handler:
    :param never_reply:
    :return:
    """
    def real_wrapper(func):
        if not inspect.iscoroutinefunction(func):
            raise ImproperlyConfigured('{} is not coroutine'.format(func.__name__))

        callback = reply(
            reply_to,
            remote_resource=remote_resource,
            remote_handler=remote_handler,
            never_reply=never_reply,
            raw_reply=raw_reply
        )(func)

        # TODO find better way
        if '.' not in func.__str__():
            from ninjin.pool import pool
            pool.connect(callback, handler_name=func.__name__)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            await callback(*args, **kwargs)
        return wrapper
    return real_wrapper
