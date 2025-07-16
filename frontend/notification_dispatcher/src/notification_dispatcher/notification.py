import logging

import telegram
from aiokafka import AIOKafkaProducer, ConsumerRecord
from pydantic import BaseModel
from telegram.constants import ParseMode

from notification_dispatcher.settings import NotificationSettings

_NOTIFICATION_SETTINGS = NotificationSettings()
_LOGGER = logging.getLogger(__name__)
_producer = None


class Notification(BaseModel):
    chat_id: int
    message: str

    def __init__(self, chat_id: int, message: str):
        super().__init__(chat_id=chat_id, message=message)

    @staticmethod
    def from_kafka_message(kafka_message: ConsumerRecord[bytes, bytes]) -> "Notification":
        if kafka_message.key is None or kafka_message.value is None:
            raise ValueError("Received message with missing key or value")

        chat_id = int.from_bytes(kafka_message.key)
        message_text = kafka_message.value.decode("utf-8")
        return Notification(chat_id=chat_id, message=message_text)

    @staticmethod
    async def start_producer() -> None:
        global _producer
        _producer = AIOKafkaProducer(bootstrap_servers=_NOTIFICATION_SETTINGS.KAFKA_SERVER)
        await _producer.start()

    async def send_message(self, bot: telegram.Bot) -> None:
        """
        Sends a notification message using the provided Telegram bot.
        """
        try:
            await bot.send_message(
                chat_id=self.chat_id,
                text=self.message,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        except Exception as e:
            _LOGGER.error(f"Failed to send message to chat {self.chat_id}: {e}")
            raise

    async def send_notification(self) -> None:
        """
        Sends a notification by producing a message to the Kafka topic.
        """
        assert _producer is not None, "Producer is not initialized. Call start_producer() first."

        try:
            key = self.chat_id.to_bytes(8, "big")
            value = self.message.encode("utf-8")
            await _producer.send(_NOTIFICATION_SETTINGS.KAFKA_TOPIC, key=key, value=value)
            # LOGGER.info(f"Notification sent to chat {self.chat_id}")
        except Exception as e:
            _LOGGER.error(f"Failed to send notification to Kafka: {e}")
            raise
