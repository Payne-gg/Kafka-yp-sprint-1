from kafka import KafkaProducer
from message import Message
import uuid
import logging
import time
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageProducer:
    def __init__(self, bootstrap_servers: list[str]):
        """
        Инициализация продюсера с гарантией доставки At Least Once.
        
        :param bootstrap_servers: Список адресов брокеров Kafka
        """
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            acks='all',  # Гарантия At Least Once - ждем подтверждения от всех реплик
            retries=5,   # Количество повторных попыток
            retry_backoff_ms=1000,  # Задержка между повторными попытками
            max_in_flight_requests_per_connection=1,  # Для сохранения порядка сообщений
            compression_type=None  # Отключаем сжатие
        )

    def send_message(self, topic: str, content: str) -> Optional[Message]:
        """
        Отправка сообщения в Kafka.
        
        :param topic: Имя топика
        :param content: Содержимое сообщения
        :return: Объект сообщения в случае успеха, None в случае ошибки
        """
        try:
            message = Message(id=str(uuid.uuid4()), content=content)
            json_data = message.to_json()
            
            if json_data:
                logger.info(f"Отправка сообщения: {message}")
                future = self.producer.send(
                    topic,
                    json_data.encode('utf-8')
                )
                # Ждем подтверждения отправки
                future.get(timeout=10)
                return message
            return None
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            return None

    def close(self):
        """Закрытие продюсера."""
        self.producer.close()

if __name__ == "__main__":
    producer = MessageProducer(['localhost:9093', 'localhost:9095', 'localhost:9097'])
    
    try:
        for i in range(20):  # Отправим 20 сообщений для теста
            message = producer.send_message('python-topic', f'Тестовое сообщение {i}')
            if message:
                logger.info(f"Сообщение успешно отправлено: {message}")
            time.sleep(1)  # Пауза между сообщениями
    finally:
        producer.close() 