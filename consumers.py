from kafka import KafkaConsumer
from message import Message
import logging
from typing import Optional
import threading
import time
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        self.group_id = group_id
        
        # Добавляем задержку перед подключением
        logger.info(f"Ожидание 10 секунд перед подключением консьюмера {group_id}...")
        time.sleep(10)
        
        try:
            self.consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='earliest',
                enable_auto_commit=False,  # Отключаем автокоммит
                max_poll_interval_ms=300000,  # 5 минут на обработку
                session_timeout_ms=60000,     # 1 минута таймаут сессии
                heartbeat_interval_ms=20000,  # Heartbeat каждые 20 секунд
                max_poll_records=100,         # Максимальное количество записей за один poll
                fetch_max_wait_ms=500,        # Максимальное время ожидания данных
                fetch_min_bytes=1             # Минимальный размер данных для получения
            )
            logger.info(f"Консьюмер {group_id} успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации консьюмера {group_id}: {e}")
            raise

        self.running = False
        self.thread = None

    def process_message(self, message: Message) -> None:
        """Обработка сообщения."""
        raise NotImplementedError()

    def start(self) -> None:
        """Запуск консьюмера в отдельном потоке."""
        self.running = True
        self.thread = threading.Thread(target=self._consume)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Консьюмер {self.group_id} запущен")

    def stop(self) -> None:
        """Остановка консьюмера."""
        logger.info(f"Останавливаем консьюмер {self.group_id}")
        self.running = False
        if self.thread:
            self.thread.join(timeout=30)
        try:
            self.consumer.commit()  # Финальный коммит перед закрытием
            self.consumer.close()
            logger.info(f"Консьюмер {self.group_id} успешно остановлен")
        except Exception as e:
            logger.error(f"Ошибка при остановке консьюмера {self.group_id}: {e}")

    def _consume(self) -> None:
        """Метод потребления сообщений."""
        raise NotImplementedError()

class SingleMessageConsumer(BaseConsumer):
    def __init__(self, bootstrap_servers: list[str], topic: str, instance_id: str = "1"):
        """
        Консьюмер для обработки одиночных сообщений.
        
        :param bootstrap_servers: Список адресов брокеров Kafka
        :param topic: Имя топика
        :param instance_id: Идентификатор экземпляра консьюмера
        """
        self.instance_id = instance_id
        super().__init__(
            bootstrap_servers=bootstrap_servers,
            topic=topic,
            group_id=f'single_message_group_{instance_id}'
        )

    def process_message(self, message: Message) -> None:
        """Обработка одиночного сообщения."""
        logger.info(f"SingleMessageConsumer [{self.instance_id}] обработал сообщение: {message}")

    def _consume(self) -> None:
        while self.running:
            try:
                # Получаем одно сообщение
                messages = self.consumer.poll(timeout_ms=1000, max_records=1)
                
                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            message_data = record.value.decode('utf-8')
                            message = Message.from_json(message_data)
                            if message:
                                self.process_message(message)
                                # Коммитим после успешной обработки
                                self.consumer.commit()
                        except json.JSONDecodeError as e:
                            logger.error(f"Ошибка декодирования JSON в сообщении: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Ошибка обработки сообщения: {e}")
                            continue
            except Exception as e:
                logger.error(f"Ошибка в консьюмере {self.group_id}: {e}")
                time.sleep(5)  # Пауза перед повторной попыткой
                continue

class BatchMessageConsumer(BaseConsumer):
    def __init__(self, bootstrap_servers: list[str], topic: str, instance_id: str = "1"):
        """
        Консьюмер для пакетной обработки сообщений.
        
        :param bootstrap_servers: Список адресов брокеров Kafka
        :param topic: Имя топика
        :param instance_id: Идентификатор экземпляра консьюмера
        """
        self.instance_id = instance_id
        super().__init__(
            bootstrap_servers=bootstrap_servers,
            topic=topic,
            group_id=f'batch_message_group_{instance_id}'
        )

    def process_message(self, message: Message) -> None:
        """Обработка сообщения в пакете."""
        logger.info(f"BatchMessageConsumer [{self.instance_id}] обработал сообщение: {message}")

    def _consume(self) -> None:
        while self.running:
            try:
                # Получаем пакет сообщений
                messages = self.consumer.poll(timeout_ms=1000, max_records=10)
                
                if not messages:
                    continue

                processed_messages = []
                
                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            message_data = record.value.decode('utf-8')
                            message = Message.from_json(message_data)
                            if message:
                                self.process_message(message)
                                processed_messages.append(message)
                        except json.JSONDecodeError as e:
                            logger.error(f"Ошибка декодирования JSON в сообщении: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Ошибка обработки сообщения: {e}")
                            continue

                if processed_messages:
                    try:
                        # Коммитим оффсеты после обработки всей пачки
                        self.consumer.commit()
                        logger.info(f"BatchMessageConsumer [{self.instance_id}] успешно обработал {len(processed_messages)} сообщений")
                    except Exception as e:
                        logger.error(f"Ошибка коммита в консьюмере {self.group_id}: {e}")
            except Exception as e:
                logger.error(f"Ошибка в консьюмере {self.group_id}: {e}")
                time.sleep(5)  # Пауза перед повторной попыткой
                continue

if __name__ == "__main__":
    import sys
    instance_id = sys.argv[1] if len(sys.argv) > 1 else "1"
    
    bootstrap_servers = ['localhost:9093', 'localhost:9095', 'localhost:9097']
    topic = 'python-topic'

    # Создаем и запускаем оба типа консьюмеров
    single_consumer = SingleMessageConsumer(bootstrap_servers, topic, instance_id)
    batch_consumer = BatchMessageConsumer(bootstrap_servers, topic, instance_id)

    try:
        single_consumer.start()
        batch_consumer.start()

        # Даем консьюмерам поработать бесконечно
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения работы")
    finally:
        single_consumer.stop()
        batch_consumer.stop() 