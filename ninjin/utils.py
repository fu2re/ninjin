import asyncio
from typing import Tuple

import aio_pika
from dynaconf import settings


async def init_aio_pika(loop=None) -> Tuple[aio_pika.RobustConnection,
                                            aio_pika.RobustExchange,
                                            aio_pika.RobustChannel]:
    if loop is None:
        loop = asyncio.get_event_loop()

    connection = await aio_pika.connect_robust(
        host=settings.BROKER_NAME,
        port=settings.BROKER_PORT,
        login=settings.BROKER_LOGIN,
        password=settings.BROKER_PASSWORD,
        loop=loop
    )
    channel = await connection.channel()

    # Fair Dispatch. This tells RabbitMQ not to give more than one message to a worker at a time
    # NOTICE If all the workers are busy, your queue can fill up.
    # await channel.set_qos(prefetch_count=1)

    exchange = await channel.declare_exchange(
        name=settings.BROKER_EXCHANGE_NAME,
        type=settings.BROKER_EXCHANGE_TYPE,
        durable=settings.BROKER_EXCHANGE_DURABLE,
        auto_delete=settings.BROKER_EXCHANGE_AUTO_DELETE
    )
    return connection, exchange, channel


async def close_aio_pika(connection: aio_pika.RobustConnection) -> None:
    await connection.close()
