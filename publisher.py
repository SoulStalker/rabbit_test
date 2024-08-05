import asyncio
import json
from datetime import datetime, timedelta, timezone, time

import aiormq


async def publish_message():
    # Подключаемся к RabbitMQ
    connection = await aiormq.connect("")

    # Создаем канал
    channel = await connection.channel()

    # Объявляем точку обмена (создается, если не существует)
    await channel.exchange_declare('main_exchange', exchange_type='direct')

    # Определяем время, когда сообщение должно быть обработано
    # scheduled_time = (datetime.now(timezone.utc) + timedelta(seconds=15)).isoformat()
    scheduled_time = datetime.combine(datetime.today(), time(16, 12)).isoformat()

    # Создаем словарь, из которого будет сформировано тело сообщения
    body = {
        'text': f'Hello from RabbitMQ! This message for time: {scheduled_time}',
    }
    # Отправляем сообщение в `main_exchange`
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

    # Закрываем соединение
    await connection.close()

asyncio.run(publish_message())
