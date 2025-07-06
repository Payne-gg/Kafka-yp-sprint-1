# Kafka Python Demo

Демонстрационный проект для работы с Apache Kafka на Python. Реализует паттерн публикации-подписки с гарантией доставки сообщений "At Least Once".

## Требования

- Python 3.8+ (рекомендуется Python 3.9)
- Docker и Docker Compose
- Windows 10/11 или Linux

## Быстрый старт

### 1. Настройка Python окружения

```bash
# Создание виртуального окружения
python -m venv venv

# Активация окружения
# Windows:
venv\Scripts\activate
# Linux/MacOS:
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Запуск Kafka в Docker

```bash
# Запуск контейнеров
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Остановка контейнеров
docker-compose down

# Полная очистка (включая тома)
docker-compose down -v
docker system prune -f
```

### 3. Запуск приложения

```bash
# Запуск консьюмеров (в отдельном терминале)
python consumers.py

# Запуск продюсера (в отдельном терминале)
python producer.py
```

## Структура проекта

### `message.py`
Базовый класс для сообщений с поддержкой сериализации в JSON:
- Уникальный ID для каждого сообщения
- Метка времени создания
- Полезная нагрузка в поле content

### `producer.py`
Продюсер Kafka с гарантией доставки "At Least Once":
- Подтверждение записи от всех реплик (acks='all')
- Автоматические повторные попытки при ошибках
- Сохранение порядка сообщений
- Обработка ошибок и логирование

### `consumers.py`
Два типа консьюмеров для демонстрации разных паттернов потребления:
- SingleMessageConsumer: обработка сообщений по одному
- BatchMessageConsumer: пакетная обработка сообщений

### `docker-compose.yml`
Конфигурация кластера Kafka:
- 3 брокера для отказоустойчивости
- ZooKeeper для координации
- Настройки томов для сохранения данных
- Конфигурация портов и сетевого взаимодействия

## Особенности реализации

- Использование kafka-python-ng для совместимости с Python 3.13
- Топик "python-topic" с 3 партициями и фактором репликации 2
- Логирование всех операций для отладки
- Graceful shutdown при завершении работы

## Возможные проблемы

1. **Ошибка подключения к брокеру**
   ```
   kafka.errors.NoBrokersAvailable: NoBrokersAvailable
   ```
   Решение: Проверьте, что все контейнеры запущены через `docker-compose ps`

2. **Ошибка создания топика**
   ```
   kafka.errors.TopicAlreadyExistsError: TopicAlreadyExistsError
   ```
   Решение: Топик уже существует, можно продолжать работу

## Дополнительные команды

### Работа с Docker

```bash
# Просмотр логов конкретного сервиса
docker-compose logs kafka1

# Перезапуск одного сервиса
docker-compose restart kafka1

# Масштабирование (если настроено)
docker-compose up -d --scale kafka=3

# Очистка неиспользуемых ресурсов
docker system prune --volumes
```

### Мониторинг Kafka

```bash
# Просмотр списка топиков
docker-compose exec kafka1 kafka-topics.sh --list --bootstrap-server localhost:9093

# Описание топика
docker-compose exec kafka1 kafka-topics.sh --describe --topic python-topic --bootstrap-server localhost:9093

# Просмотр групп потребителей
docker-compose exec kafka1 kafka-consumer-groups.sh --list --bootstrap-server localhost:9093
```

## Лицензия

MIT 