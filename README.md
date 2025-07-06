# Kafka Producer-Consumer Application

Приложение демонстрирует работу с Apache Kafka, включая гарантированную доставку сообщений, сериализацию и масштабирование.

## Структура проекта

### Классы

1. **Message** (`message.py`)
   - Базовый класс для сообщений
   - Поля: id (UUID), content (строка), timestamp (ISO формат)
   - Методы сериализации/десериализации в JSON
   - Валидация данных при создании

2. **MessageProducer** (`producer.py`)
   - Отправка сообщений с гарантией At Least Once
   - Настройки надежности:
     * `acks='all'` - подтверждение от всех реплик
     * `retries=5` - повторные попытки при ошибках
     * `retry_backoff_ms=1000` - пауза между попытками
     * `max_in_flight_requests_per_connection=1` - сохранение порядка

3. **Consumers** (`consumers.py`)
   - `SingleMessageConsumer`: обработка одиночных сообщений
   - `BatchMessageConsumer`: пакетная обработка
   - Поддержка масштабирования через instance_id
   - Настройки надежности и производительности

## Установка и запуск

### Предварительные требования

- Docker и Docker Compose
- Python 3.9+
- Виртуальное окружение Python

### Шаги установки

1. **Клонирование репозитория**
   ```bash
   git clone <repository-url>
   cd kafka-project
   ```

2. **Создание виртуального окружения**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. **Установка зависимостей**
   ```bash
   pip install -r requirements.txt
   ```

4. **Запуск Kafka кластера**
   ```bash
   docker-compose up -d
   ```

5. **Создание топика**
   ```bash
   docker exec kafka1 kafka-topics --create --topic python-topic \
   --bootstrap-server kafka1:9092 --partitions 3 --replication-factor 2
   ```

### Проверка работы

1. **Запуск консьюмеров**
   ```bash
   # В первом терминале
   python consumers.py 1  # instance_id = 1
   
   # Во втором терминале
   python consumers.py 2  # instance_id = 2
   ```

2. **Запуск продюсера**
   ```bash
   # В третьем терминале
   python producer.py
   ```

3. **Проверка гарантий доставки**
   - Остановите один из брокеров:
     ```bash
     docker stop kafka2
     ```
   - Отправьте сообщения через producer.py
   - Убедитесь, что сообщения доставлены (логи консьюмеров)
   - Запустите брокер обратно:
     ```bash
     docker start kafka2
     ```

4. **Проверка масштабирования**
   - Запустите несколько экземпляров консьюмеров
   - Проверьте распределение партиций между ними
   - Посмотрите логи обработки сообщений

## Мониторинг

1. **Проверка топика**
   ```bash
   docker exec kafka1 kafka-topics --describe --topic python-topic \
   --bootstrap-server kafka1:9092
   ```

2. **Просмотр групп потребителей**
   ```bash
   docker exec kafka1 kafka-consumer-groups --bootstrap-server kafka1:9092 \
   --describe --group single_message_group_1
   ```

## Управление Docker-контейнерами

### Запуск кластера

1. Запуск всех сервисов:
```bash
docker-compose up -d
```

2. Запуск конкретного сервиса:
```bash
docker-compose up -d kafka1  # Запуск только первого брокера
docker-compose up -d zookeeper  # Запуск только ZooKeeper
```

3. Масштабирование консьюмеров:
```bash
docker-compose up -d --scale consumer=3  # Запуск 3 экземпляров консьюмера
```

### Остановка контейнеров

1. Остановка всех сервисов:
```bash
docker-compose down  # Остановка и удаление контейнеров
docker-compose stop  # Только остановка без удаления
```

2. Остановка конкретного сервиса:
```bash
docker-compose stop kafka1  # Остановка первого брокера
docker-compose stop consumer  # Остановка всех консьюмеров
```

### Просмотр логов

1. Логи всех сервисов:
```bash
docker-compose logs -f  # В реальном времени
docker-compose logs    # Просмотр существующих логов
```

2. Логи конкретного сервиса:
```bash
docker-compose logs -f kafka1  # Логи первого брокера
docker-compose logs -f consumer  # Логи всех консьюмеров
```

### Управление данными

1. Очистка всех данных:
```bash
docker-compose down -v  # Удаление контейнеров и томов
```

2. Пересоздание контейнеров:
```bash
docker-compose up -d --force-recreate  # Пересоздание всех контейнеров
```

### Проверка состояния

1. Статус контейнеров:
```bash
docker-compose ps  # Список всех контейнеров и их состояний
```

2. Использование ресурсов:
```bash
docker stats  # Мониторинг использования CPU, памяти и сети
```

### Важные замечания

1. Порядок запуска:
   - Сначала запускается ZooKeeper
   - Затем брокеры Kafka
   - После этого консьюмеры
   - Docker Compose автоматически соблюдает этот порядок

2. Время запуска:
   - Дождитесь полного запуска ZooKeeper (10-15 секунд)
   - Брокерам нужно 20-30 секунд для инициализации
   - Консьюмеры имеют встроенную задержку 10 секунд

3. Проверка готовности:
   - Используйте `docker-compose logs` для проверки статуса
   - Убедитесь, что все сервисы успешно стартовали
   - Проверьте доступность UI по адресу localhost:8080

## Особенности реализации

1. **Гарантии доставки**
   - At Least Once через настройки продюсера
   - Подтверждение от всех реплик (acks='all')
   - Повторные попытки при ошибках

2. **Сериализация**
   - JSON формат для сообщений
   - Валидация данных
   - Обработка ошибок сериализации

3. **Масштабирование**
   - Поддержка multiple consumer instances
   - Уникальные group_id для разных типов консьюмеров
   - Балансировка партиций

4. **Отказоустойчивость**
   - Работа при отказе брокера
   - Автоматическое переподключение
   - Сохранение порядка сообщений
