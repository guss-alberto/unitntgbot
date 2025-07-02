import asyncio
import logging

from aiokafka import AIOKafkaConsumer, ConsumerRecord
from pydantic import BaseModel, ValidationError
from telegram import Bot
from telegram.constants import ParseMode

from unitntgbot.notification_dispatcher.settings import settings

logger = logging.getLogger(__name__)


class NotificationMessage(BaseModel):
    chat_id: int
    html_message: str


BOT = Bot(token=settings.TELEGRAM_BOT_TOKEN)


def entrypoint() -> None:
    asyncio.run(listen_topics())


async def listen_topics() -> None:
    consumer = AIOKafkaConsumer(settings.KAFKA_TOPIC, bootstrap_servers=settings.KAFKA_SERVER)

    await consumer.start()
    try:
        async for msg in consumer:
            await handle_message(msg)

    finally:
        await consumer.stop()


async def handle_message(kafka_message: ConsumerRecord) -> None:
    try:
        message_content = NotificationMessage.model_validate_json(kafka_message.value)
    except ValidationError:
        logger.error("Invalid message format: %s", kafka_message.value)
        return

    await send_notification(message_content)


async def send_notification(message: NotificationMessage) -> None:
    await BOT.send_message(chat_id=message.chat_id, text=message.html_message, parse_mode=ParseMode.HTML)
