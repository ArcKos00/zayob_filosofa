# WhatsApp Sender API

RESTful API для відправки повідомлень через WhatsApp Web

## Вимоги

- **Python 3.12** (обов'язково)
- Docker & Docker Compose (для Selenium Grid)
- pip та venv

## Встановлення Python 3.12

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
```

## Швидкий старт

### 1. Створення віртуального середовища

```bash
# Автоматичне створення venv та встановлення залежностей
chmod +x setup.sh
./setup.sh
```

Або вручну:
```bash
# Створення venv з Python 3.12
python3.12 -m venv venv

# Активація
source venv/bin/activate

# Встановлення залежностей
pip install -r requirements.txt
```

### 2. Запуск Selenium Grid

```bash
docker-compose up -d
```

### 3. Запуск WhatsApp сесії

```bash
source venv/bin/activate
python whatsapp_session.py
```

Відскануйте QR-код у браузері що відкриється.

### 4. Запуск API

У новому терміналі:
```bash
source venv/bin/activate
python send_whatsapp.py
```

API буде доступне за адресою: http://localhost:8000

Swagger документація: http://localhost:8000/docs

## Використання API

### Відправка повідомлення

```bash
curl -X POST "http://localhost:8000/send-message" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "Іван Петренко",
    "message": "Привіт! Як справи?"
  }'
```

### Перевірка стану

```bash
curl http://localhost:8000/health
```

## Структура проекту

- `whatsapp_session.py` - Запуск та авторизація у WhatsApp Web
- `send_whatsapp.py` - FastAPI сервер для відправки повідомлень
- `requirements.txt` - Python залежності
- `runtime.txt` - Версія Python
- `setup.sh` - Скрипт автоматичного налаштування
- `docker-compose.yml` - Конфігурація Selenium Grid

## Troubleshooting

### Проблема зі створенням профілю
Якщо виникає помилка "cannot create default profile directory":
1. Перезапустіть Docker: `docker-compose down && docker-compose up -d`
2. Перевірте права доступу до директорії whatsapp_session/

### Сесія втрачена
Якщо API повідомляє про втрачену сесію:
1. Перезапустіть `whatsapp_session.py`
2. Заново відскануйте QR-код
