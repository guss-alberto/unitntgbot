import asyncio
import logging

from kafka import KafkaConsumer
from pydantic import ValidationError
from telegram import Bot
from telegram.constants import ParseMode

from notification_dispatcher.notification import Notification
from notification_dispatcher.settings import BotSettings, NotificationSettings

BOT_SETTINGS = BotSettings()
NOTIFICATION_SETTINGS = NotificationSettings()

LOGGER = logging.getLogger(__name__)
BOT = Bot(token=BOT_SETTINGS.TELEGRAM_BOT_TOKEN)


def main() -> None:
    asyncio.run(listen_topic())


async def listen_topic() -> None:
    consumer = KafkaConsumer(
        group_id=None,
        bootstrap_servers=NOTIFICATION_SETTINGS.KAFKA_SERVER,
    )
    consumer.subscribe([NOTIFICATION_SETTINGS.KAFKA_TOPIC])
    
    LOGGER.warning("Started listening to Kafka topic: %s", NOTIFICATION_SETTINGS.KAFKA_TOPIC)

    for msg in consumer:
        await handle_message(msg)


async def handle_message(kafka_message) -> None:
    if kafka_message.key is None or kafka_message.value is None:
        LOGGER.warning("Received message with missing key or value")
        return

    try:
        chat_id, message = Notification.from_kafka_message(kafka_message)
    except UnicodeDecodeError:
        LOGGER.error("Invalid unicode in message: %s", kafka_message.value)
        return
    except ValidationError:
        LOGGER.error("Invalid data in message: %s", kafka_message.value)
        return
    
    await BOT.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.HTML,
    )
    LOGGER.warning(f"Notification sent to chat {chat_id}")
