import json
from dataclasses import dataclass
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Message:
    id: str
    content: str
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_json(self) -> str:
        """Сериализация сообщения в JSON."""
        try:
            return json.dumps({
                'id': self.id,
                'content': self.content,
                'timestamp': self.timestamp
            })
        except Exception as e:
            logger.error(f"Ошибка сериализации: {e}")
            return None

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Десериализация сообщения из JSON."""
        try:
            data = json.loads(json_str)
            return cls(
                id=data['id'],
                content=data['content'],
                timestamp=data['timestamp']
            )
        except Exception as e:
            logger.error(f"Ошибка десериализации: {e}")
            return None 