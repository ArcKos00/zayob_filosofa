#!/usr/bin/env python3
"""
WhatsApp Session Manager
Запускає браузер і авторизується у WhatsApp Web.
Зберігає session_id для повторного використання.
"""
import argparse
import time
import os
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Файл для збереження session_id
SESSION_FILE = os.path.join(os.path.dirname(__file__), '.whatsapp_session.json')


def get_active_sessions(driver_url):
    """Отримує список активних сесій з Selenium Grid"""
    try:
        status_url = driver_url.replace('/wd/hub', '/status')
        response = requests.get(status_url, timeout=5)
        data = response.json()

        sessions = []
        for node in data['value']['nodes']:
            for slot in node['slots']:
                if slot['session']:
                    sessions.append(slot['session']['sessionId'])
        return sessions
    except Exception as e:
        print(f"⚠️ Не вдалося отримати активні сесії: {e}")
        return []


def save_session_id(session_id):
    """Зберігає session_id у файл"""
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump({'session_id': session_id}, f)
        print(f"✓ Session ID збережено: {session_id[:8]}...")
    except Exception as e:
        print(f"⚠️ Не вдалося зберегти session ID: {e}")


def load_session_id():
    """Завантажує session_id з файлу"""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f).get('session_id')
        except:
            pass
    return None


def clear_session_file():
    """Видаляє файл з session_id"""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
        print("✓ Файл сесії видалено")


def start_whatsapp_session(driver_url='http://localhost:4444/wd/hub', timeout=60, keep_open=True):
    """
    Запускає браузер і авторизується у WhatsApp Web.

    :param driver_url: URL Selenium Remote WebDriver
    :param timeout: Час очікування авторизації в секундах
    :param keep_open: Залишити браузер відкритим (за замовчуванням True)
    :return: WebDriver instance або None
    """
    # Перевіряємо чи вже є активна сесія
    existing_session_id = load_session_id()
    if existing_session_id:
        active_sessions = get_active_sessions(driver_url)
        if existing_session_id in active_sessions:
            print(f"✓ Вже є активна сесія: {existing_session_id[:8]}...")
            print("Використовуйте send_whatsapp.py для відправки повідомлень")
            return None
        else:
            print("⚠️ Збережена сесія більше не активна. Створюю нову...")
            clear_session_file()

    print("Створюю нову сесію браузера...")
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Remote(command_executor=driver_url, options=options)
    save_session_id(driver.session_id)

    try:
        print("Відкриваю WhatsApp Web...")
        driver.get('https://web.whatsapp.com')
        wait = WebDriverWait(driver, timeout)

        # Перевіряємо чи вже залогінені (наприклад, через cookies)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'pane-side')))
            print("✓ Вже авторизовані!")
        except Exception:
            print(f"Чекаю на авторизацію (скануйте QR-код). Таймаут: {timeout} секунд...")
            wait.until(EC.presence_of_element_located((By.ID, 'pane-side')))
            print("✓ Авторизація успішна!")

        # Додатковий час для завантаження всіх чатів
        time.sleep(2)

        print("=" * 60)
        print("✅ WhatsApp сесія активна!")
        print(f"Session ID: {driver.session_id[:8]}...")
        print("=" * 60)
        print()
        print("Тепер можна відправляти повідомлення через send_whatsapp.py:")
        print("  python send_whatsapp.py --contact 'Name' --message 'Text'")
        print()

        if keep_open:
            print("⚠️ Браузер залишається відкритим.")
            print("Натисніть Ctrl+C для завершення...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nЗавершення роботи...")
                driver.quit()
                clear_session_file()
                print("Браузер закрито, сесія видалена")

        return driver

    except Exception as e:
        print(f"✗ Помилка: {e}")
        clear_session_file()
        if driver:
            driver.quit()
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Запуск і авторизація у WhatsApp Web через Selenium'
    )
    parser.add_argument(
        '--driver',
        default='http://localhost:4444/wd/hub',
        help='URL Selenium Remote WebDriver (за замовчуванням: http://localhost:4444/wd/hub)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Час очікування авторизації в секундах (за замовчуванням: 60)'
    )
    parser.add_argument(
        '--no-keep-open',
        action='store_true',
        help='Закрити браузер після авторизації (за замовчуванням залишається відкритим)'
    )

    args = parser.parse_args()

    start_whatsapp_session(
        driver_url=args.driver,
        timeout=args.timeout,
        keep_open=not args.no_keep_open
    )
