import json
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Optional
import uuid

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Message:
    id: str
    content: str
    timestamp: Optional[str] = None

    def __post_init__(self):
        """Валидация и инициализация после создания объекта."""
        # Валидация ID
        try:
            uuid.UUID(self.id)
        except ValueError:
            raise ValueError("ID должен быть валидным UUID")

        # Валидация content
        if not self.content or not isinstance(self.content, str):
            raise ValueError("Content не может быть пустым и должен быть строкой")

        # Установка timestamp
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        else:
            # Проверка формата timestamp
            try:
                datetime.fromisoformat(self.timestamp)
            except ValueError:
                raise ValueError("Timestamp должен быть в формате ISO")

    def to_json(self) -> Optional[str]:
        """
        Сериализация сообщения в JSON.
        
        Returns:
            str: JSON строка или None в случае ошибки
        """
        try:
            json_data = {
                'id': self.id,
                'content': self.content,
                'timestamp': self.timestamp
            }
            result = json.dumps(json_data)
            logger.debug(f"Сообщение успешно сериализовано: {json_data}")
            return result
        except Exception as e:
            logger.error(f"Ошибка сериализации сообщения {self.id}: {str(e)}")
            return None

    @classmethod
    def from_json(cls, json_str: str) -> Optional['Message']:
        """
        Десериализация сообщения из JSON.
        
        Args:
            json_str: JSON строка
            
        Returns:
            Message: Объект сообщения или None в случае ошибки
        """
        try:
            if not isinstance(json_str, str):
                raise ValueError("Входные данные должны быть строкой")

            data = json.loads(json_str)
            
            # Проверка обязательных полей
            required_fields = {'id', 'content', 'timestamp'}
            if not all(field in data for field in required_fields):
                missing = required_fields - set(data.keys())
                raise ValueError(f"Отсутствуют обязательные поля: {missing}")

            message = cls(
                id=data['id'],
                content=data['content'],
                timestamp=data['timestamp']
            )
            logger.debug(f"Сообщение успешно десериализовано: {message}")
            return message
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Ошибка десериализации: {str(e)}")
            return None

    def __str__(self) -> str:
        """Строковое представление для логирования."""
        return f"Message(id='{self.id}', content='{self.content}', timestamp='{self.timestamp}')" 