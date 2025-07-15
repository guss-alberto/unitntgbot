import asyncio

from aiokafka import AIOKafkaProducer

KAFKA_SERVER = "localhost:9094"
KAFKA_TOPIC = "notifications"


async def send():
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_SERVER)
    await producer.start()
    try:
        tg_id = 648954207
        await producer.send_and_wait(KAFKA_TOPIC, "_Hello from test_".encode(), key=tg_id.to_bytes(8))
        print("Message sent!")
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(send())
