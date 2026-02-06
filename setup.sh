#!/bin/bash
# Script для створення віртуального середовища та встановлення залежностей

echo "Перевірка версії Python..."
python3 --version

# Перевірка чи встановлено Python 3.12
if ! python3.12 --version &> /dev/null; then
    echo "⚠️  Python 3.12 не знайдено!"
    echo "Встановіть Python 3.12:"
    echo "  sudo apt update"
    echo "  sudo apt install python3.12 python3.12-venv python3.12-dev"
    exit 1
fi

echo "✓ Python 3.12 знайдено"

# Видалення старого venv якщо існує
if [ -d "venv" ]; then
    echo "Видалення старого віртуального середовища..."
    rm -rf venv
fi

# Створення нового venv з Python 3.12
echo "Створення віртуального середовища з Python 3.12..."
python3.12 -m venv venv

# Активація venv
echo "Активація віртуального середовища..."
source venv/bin/activate

# Оновлення pip
echo "Оновлення pip..."
pip install --upgrade pip

# Встановлення залежностей
echo "Встановлення залежностей з requirements.txt..."
pip install -r requirements.txt

echo ""
echo "✓ Встановлення завершено!"
echo ""
echo "Для активації віртуального середовища виконайте:"
echo "  source venv/bin/activate"
echo ""
echo "Для запуску WhatsApp сесії:"
echo "  python whatsapp_session.py"
echo ""
echo "Для запуску API:"
echo "  python send_whatsapp.py"
