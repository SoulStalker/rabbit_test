import asyncio
import json
from datetime import datetime, timedelta, timezone

import aiormq


async def publish_message():
    connection = await aiormq.connect("amqp://login:password@host/")

    channel = await connection.channel()

    await channel.exchange_declare('main_exchange', exchange_type='direct')

    scheduled_time = (datetime.now(timezone.utc) + timedelta(seconds=15)).isoformat()

    body = {
        'text': 'Hello from RabbitMQ!',
    }

    await channel.basic_publish(
        body=json.dumps(body).encode('utf-8'),
        exchange='main_exchange',
        routing_key='main_routing_key',
        properties=aiormq.spec.Basic.Properties(
            headers={
                'scheduled_time': scheduled_time,
            }
        )
    )

    print(f'Published message with scheduled time: {scheduled_time}')

    await connection.close()

asyncio.run(publish_message())


