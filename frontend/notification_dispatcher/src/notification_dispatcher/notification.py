import logging

from kafka import KafkaProducer
from kafka.consumer.fetcher import ConsumerRecord

from notification_dispatcher.settings import NotificationSettings

_NOTIFICATION_SETTINGS = NotificationSettings()
_LOGGER = logging.getLogger(__name__)

_PRODUCER: KafkaProducer = KafkaProducer(bootstrap_servers=_NOTIFICATION_SETTINGS.KAFKA_SERVER)


def from_kafka_message(kafka_message: ConsumerRecord) -> tuple[int, str]:
    if kafka_message.key is None or kafka_message.value is None:
        msg = "Received message with missing key or value"
        raise ValueError(msg)

    chat_id = int.from_bytes(kafka_message.key)
    message_text = kafka_message.value.decode("utf-8")
    return chat_id, message_text

def send_notification(chat_id: int, message: str) -> None:
    try:
        key = chat_id.to_bytes(8, "big")
        value = message.encode("utf-8")
        _PRODUCER.send(_NOTIFICATION_SETTINGS.KAFKA_TOPIC, key=key, value=value)
    except Exception as e:
        _LOGGER.error("Failed to send notification to Kafka %s", e)
        raise
