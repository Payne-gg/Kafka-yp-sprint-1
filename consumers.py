from kafka import KafkaConsumer
from message import Message
import logging
from typing import Optional
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseConsumer:
    def __init__(self, bootstrap_servers: list[str], topic: str, group_id: str):
        """
        Базовый класс для консьюмеров.
        
        :param bootstrap_servers: Список адресов брокеров Kafka
        :param topic: Имя топика
        :param group_id: Идентификатор группы потребителей
        """
        self.topic = topic
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset='earliest'
        )
        self.running = False
        self.thread = None

    def process_message(self, message: Message) -> None:
        """Обработка сообщения."""
        raise NotImplementedError()

    def start(self) -> None:
        """Запуск консьюмера в отдельном потоке."""
        self.running = True
        self.thread = threading.Thread(target=self._consume)
        self.thread.start()

    def stop(self) -> None:
        """Остановка консьюмера."""
        self.running = False
        if self.thread:
            self.thread.join()
        self.consumer.close()

    def _consume(self) -> None:
        """Метод потребления сообщений."""
        raise NotImplementedError()

class SingleMessageConsumer(BaseConsumer):
    def __init__(self, bootstrap_servers: list[str], topic: str):
        """
        Консьюмер для обработки одиночных сообщений.
        
        :param bootstrap_servers: Список адресов брокеров Kafka
        :param topic: Имя топика
        """
        super().__init__(
            bootstrap_servers=bootstrap_servers,
            topic=topic,
            group_id='single_message_group'
        )
        # Включаем автоматический коммит
        self.consumer.enable_auto_commit = True

    def process_message(self, message: Message) -> None:
        """Обработка одиночного сообщения."""
        logger.info(f"SingleMessageConsumer обработал сообщение: {message}")

    def _consume(self) -> None:
        try:
            while self.running:
                # Получаем одно сообщение
                messages = self.consumer.poll(timeout_ms=1000, max_records=1)
                
                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            message = Message.from_json(record.value.decode('utf-8'))
                            if message:
                                self.process_message(message)
                        except Exception as e:
                            logger.error(f"Ошибка обработки сообщения: {e}")
        except Exception as e:
            logger.error(f"Ошибка в консьюмере: {e}")

class BatchMessageConsumer(BaseConsumer):
    def __init__(self, bootstrap_servers: list[str], topic: str):
        """
        Консьюмер для пакетной обработки сообщений.
        
        :param bootstrap_servers: Список адресов брокеров Kafka
        :param topic: Имя топика
        """
        super().__init__(
            bootstrap_servers=bootstrap_servers,
            topic=topic,
            group_id='batch_message_group'
        )
        # Отключаем автоматический коммит
        self.consumer.enable_auto_commit = False
        
        # Настройка для получения минимум 10 сообщений
        self.consumer.config['fetch.min.bytes'] = 1024  # Минимальный размер данных
        self.consumer.config['fetch.max.wait.ms'] = 500  # Максимальное время ожидания

    def process_message(self, message: Message) -> None:
        """Обработка сообщения в пакете."""
        logger.info(f"BatchMessageConsumer обработал сообщение: {message}")

    def _consume(self) -> None:
        try:
            while self.running:
                # Получаем пакет сообщений
                messages = self.consumer.poll(timeout_ms=1000, max_records=10)
                
                if not messages:
                    continue

                processed_messages = []
                
                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            message = Message.from_json(record.value.decode('utf-8'))
                            if message:
                                self.process_message(message)
                                processed_messages.append(message)
                        except Exception as e:
                            logger.error(f"Ошибка обработки сообщения: {e}")

                if processed_messages:
                    try:
                        # Коммитим оффсеты после обработки всей пачки
                        self.consumer.commit(async_=False)
                        logger.info(f"Успешно обработано {len(processed_messages)} сообщений")
                    except Exception as e:
                        logger.error(f"Ошибка коммита: {e}")
        except Exception as e:
            logger.error(f"Ошибка в консьюмере: {e}")

if __name__ == "__main__":
    bootstrap_servers = ['localhost:9093', 'localhost:9095', 'localhost:9097']
    topic = 'python-topic'

    # Создаем и запускаем оба типа консьюмеров
    single_consumer = SingleMessageConsumer(bootstrap_servers, topic)
    batch_consumer = BatchMessageConsumer(bootstrap_servers, topic)

    try:
        single_consumer.start()
        batch_consumer.start()

        # Даем консьюмерам поработать
        time.sleep(60)
    finally:
        single_consumer.stop()
        batch_consumer.stop() 