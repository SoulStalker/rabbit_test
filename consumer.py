import asyncio
from datetime import datetime, timezone

import aiormq
from aiormq.abc import DeliveredMessage


async def on_message(message: DeliveredMessage):
    try:
        headers = message.header.properties.headers

        scheduled_time = datetime.fromisoformat(headers.get('scheduled_time')).astimezone(timezone.utc)

        current_time = datetime.now(timezone.utc)

        if current_time >= scheduled_time:
            print(f'Processing {message.body.decode()}')

            await asyncio.sleep(1)

            await message.channel.basic_ack(delivery_tag=message.delivery.delivery_tag)
        else:
            delay = int((scheduled_time - current_time).total_seconds() * 1000)
            print(f'Deferring {message.body.decode()}, delay: {delay} ms')

            await message.channel.basic_publish(
                body=message.body,
                routing_key='main_queue',
                exchange='delayed_exchange',
                properties=aiormq.spec.Basic.Properties(
                    headers={
                        'x-delay': delay,
                        'scheduled_time': scheduled_time.isoformat()
                    }
                ),
            )

            await message.channel.basic_reject(delivery_tag=message.delivery.delivery_tag, requeue=False)
    except Exception as e:
        print(f'Error: {e}')

        await message.channel.basic_nack(delivery_tag=message.delivery.delivery_tag, requeue=True)


async def consume(channel):
    await channel.basic_consume('main_queue', on_message, no_ack=False)


async def create_channel(connection):
    # Создаем канал
    channel = await connection.channel()

    # Объявляем точку обмена для отложенных сообщений
    await channel.exchange_declare(
        "delayed_exchange",
        exchange_type='x-delayed-message',
        arguments={'x-delayed-type': 'direct'},
    )

    # Объявляем очередь
    await channel.queue_declare('main_queue')
    # Привязываем очередь к обменнику `main_exchange`
    await channel.queue_bind('main_queue', 'main_exchange', routing_key='main_routing_key')
    # Привязываем очередь к обменнику `delayed_exchange`
    await channel.queue_bind('main_queue', 'delayed_exchange', routing_key='main_queue')
    # Определяем качество сервиса (консьюмер будет получать по одному сообщению за один раз)
    await channel.basic_qos(prefetch_count=1)
    # Возвращаем созданный и настроенный канал
    return channel


async def main():
    # Указываем параметры соединения с брокером
    connection_params = "amqp://login:password@host/"
    # Запускаем бесконечный цикл попыток соединения с брокером
    while True:
        try:
            # Подключаемся к брокеру
            connection = await aiormq.connect(connection_params)
            # Создаем канал
            channel = await create_channel(connection)
            # Запускаем прослушивание очереди
            await consume(channel)
            # Запускаем фоновую задачу для отслеживания состояния соединения
            async with connection:
                while not connection.is_closed:
                    await asyncio.sleep(1)

        except aiormq.exceptions.AMQPConnectionError as e:
            print(f'Error: {e}')

            await asyncio.sleep(5)

        except Exception as e:
            print(f'Error: {e}')


asyncio.run(main())




