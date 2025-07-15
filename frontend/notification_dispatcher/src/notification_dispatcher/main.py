import asyncio
import logging

from aiokafka import AIOKafkaConsumer, ConsumerRecord
from pydantic import BaseModel, ValidationError
from telegram import Bot
from telegram.constants import ParseMode

from notification_dispatcher.settings import settings

logger = logging.getLogger(__name__)

BOT = Bot(token=settings.TELEGRAM_BOT_TOKEN)


class NotificationMessage(BaseModel):
    chat_id: int
    message: str

    def __init__(self, chat_id: int, message: str):
        super().__init__(chat_id=chat_id, message=message)

    async def send_notification(self) -> None:
        try:
            await BOT.send_message(chat_id=self.chat_id, text=self.message, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Failed to send message to chat {self.chat_id}: {e}")
            raise


def main() -> None:
    asyncio.run(listen_topic())


async def listen_topic() -> None:
    consumer = AIOKafkaConsumer(settings.KAFKA_TOPIC, bootstrap_servers=settings.KAFKA_SERVER)

    await consumer.start()
    try:
        async for msg in consumer:
            await handle_message(msg)
    finally:
        await consumer.stop()


async def handle_message(kafka_message: ConsumerRecord[bytes, bytes]) -> None:
    if kafka_message.key is None or kafka_message.value is None:
        logger.warning("Received message with missing key or value")
        return

    try:
        chat_id = int.from_bytes(kafka_message.key)
        message_text = kafka_message.value.decode("utf-8")
        message = NotificationMessage(chat_id=chat_id, message=message_text)
    except UnicodeDecodeError:
        logger.error("Invalid unicode in message: %s", kafka_message.value)
        return
    except ValidationError:
        logger.error("Invalid data in message: %s", kafka_message.value)
        return

    await message.send_notification()
