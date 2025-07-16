import asyncio
import logging

from aiokafka import AIOKafkaConsumer, ConsumerRecord
from pydantic import ValidationError
from telegram import Bot

from notification_dispatcher.notification import Notification
from notification_dispatcher.settings import BotSettings, NotificationSettings

BOT_SETTINGS = BotSettings()
NOTIFICATION_SETTINGS = NotificationSettings()

LOGGER = logging.getLogger(__name__)
BOT = Bot(token=BOT_SETTINGS.TELEGRAM_BOT_TOKEN)


def main() -> None:
    asyncio.run(listen_topic())


async def listen_topic() -> None:
    consumer = AIOKafkaConsumer(
        NOTIFICATION_SETTINGS.KAFKA_TOPIC,
        group_id=None,
        bootstrap_servers=NOTIFICATION_SETTINGS.KAFKA_SERVER,
    )

    await consumer.start()
    LOGGER.warning("Started listening to Kafka topic: %s", NOTIFICATION_SETTINGS.KAFKA_TOPIC)

    try:
        async for msg in consumer:
            await handle_message(msg)
    finally:
        await consumer.stop()


async def handle_message(kafka_message: ConsumerRecord[bytes, bytes]) -> None:
    if kafka_message.key is None or kafka_message.value is None:
        LOGGER.warning("Received message with missing key or value")
        return

    try:
        notification = Notification.from_kafka_message(kafka_message)
    except UnicodeDecodeError:
        LOGGER.error("Invalid unicode in message: %s", kafka_message.value)
        return
    except ValidationError:
        LOGGER.error("Invalid data in message: %s", kafka_message.value)
        return

    await notification.send_message(BOT)
    LOGGER.warning(f"Notification sent to chat {notification.chat_id}")
