import asyncio
import datetime
import uuid
from zoneinfo import ZoneInfo

import aio_pika
import aiohttp
from aio_pika.abc import AbstractRobustConnection, ExchangeType
from aio_pika.pool import Pool
from loguru import logger

from core.config import settings
from schemas.entity import Notification, CreateNotificationStatus, NotificationStatus
from storages.storage import storage

instant_queue_name = "instant_queue"
scheduled_queue_name = "scheduled_queue"


async def get_timezone(user_id: uuid.UUID) -> str:
    try:
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(
                    f"http://auth:8000/api/v1/users/{user_id}/profile"
            ) as resp:
                result = await resp.json()
        user_tz = result.get('user_tz')
        return user_tz
    except:
        return 'UTC'


def calc_ttl(timezone: str) -> datetime.timedelta:
    user_time = datetime.datetime.now().astimezone(ZoneInfo(timezone)).time()
    ttl = datetime.timedelta()
    if not (datetime.time(hour=9) < user_time < datetime.time(hour=21)):
        ttl = datetime.datetime(year=2024, month=1, day=1, hour=9) - datetime.datetime(
            year=2024, month=1, day=1, hour=user_time.hour, minute=user_time.minute,
            second=user_time.second)
    if ttl < datetime.timedelta():
        ttl += datetime.timedelta(days=1)
    return ttl


async def main() -> None:
    async def get_connection() -> AbstractRobustConnection:
        return await aio_pika.connect_robust(settings.rabbit_dsn)

    connection_pool: Pool = Pool(get_connection, max_size=2)

    async def get_channel() -> aio_pika.Channel:
        async with connection_pool.acquire() as connection:
            return await connection.channel()

    channel_pool: Pool = Pool(get_channel, max_size=10)

    async def consume() -> None:
        async with (channel_pool.acquire() as channel):
            await channel.set_qos(10)
            await channel.declare_exchange('scheduler', type=ExchangeType.DIRECT)
            queue = await channel.declare_queue(
                scheduled_queue_name, durable=True, auto_delete=False,
            )

            for i in range(13):
                await channel.declare_queue(
                    f'delayed_notifications_{i}', durable=False, auto_delete=False,
                    arguments={"x-dead-letter-exchange": '',
                               "x-dead-letter-routing-key": instant_queue_name,
                               }
                )
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    try:
                        notification = Notification.model_validate_json(message.body.decode())
                    except Exception as err:
                        logger.exception(f"Validation message error: {err}")
                        await message.ack()
                        continue
                    timezone = await get_timezone(notification.user_id)
                    ttl = calc_ttl(timezone)
                    if ttl == datetime.timedelta():
                        await channel.default_exchange.publish(
                            aio_pika.Message(body=notification.model_dump_json().encode(), expiration=ttl),
                            routing_key='delayed_notifications_0',
                        )
                    else:
                        await channel.default_exchange.publish(
                            aio_pika.Message(body=notification.model_dump_json().encode(), expiration=ttl),
                            routing_key=f'delayed_notifications_{int(ttl.seconds/3600) + 1}',
                        )
                    await message.ack()
                    try:
                        async with storage.get_session() as session:
                            async with session.begin() as tr:
                                await storage.create_notification_status(CreateNotificationStatus(
                                    notification_id=notification.notification_id,
                                    status=NotificationStatus.SCHEDULED,
                                ))
                                await tr.commit()
                    except Exception as err:
                        logger.exception(f"Couldn't change status: {err}")
                        continue

    async with connection_pool, channel_pool:
        task = asyncio.create_task(consume())
        await task


if __name__ == "__main__":
    asyncio.run(main())
