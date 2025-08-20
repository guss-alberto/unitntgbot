import logging

from kafka import KafkaProducer

from notification_dispatcher.settings import NotificationSettings

_NOTIFICATION_SETTINGS = NotificationSettings()
_LOGGER = logging.getLogger(__name__)

class Notification:
    def __init__(self):
        self._producer = KafkaProducer(bootstrap_servers=_NOTIFICATION_SETTINGS.KAFKA_SERVER)
        
    def __del__(self):
        self._producer.close()
        
    @staticmethod
    def from_kafka_message(kafka_message) -> tuple[int, str]:
        if kafka_message.key is None or kafka_message.value is None:
            raise ValueError("Received message with missing key or value")

        chat_id = int.from_bytes(kafka_message.key)
        message_text = kafka_message.value.decode("utf-8")
        return chat_id, message_text

    async def send_notification(self, chat_id: int, message: str) -> None:
        try:
            key = chat_id.to_bytes(8, "big")
            value = message.encode("utf-8")
            self._producer.send(_NOTIFICATION_SETTINGS.KAFKA_TOPIC, key=key, value=value)
        except Exception as e:
            _LOGGER.error(f"Failed to send notification to Kafka: {e}")
            raise
