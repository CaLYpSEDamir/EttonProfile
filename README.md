# EttonProfile

1. Запускаем RabbitMQ сервер
2. Переходим в директорию, где лежит main.py, окрываем 2 консоли
3. В первой запускаем Celery: celery -A tasks worker
4. Во второй запускаем проект: python main.py
