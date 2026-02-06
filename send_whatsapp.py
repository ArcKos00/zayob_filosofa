#!/usr/bin/env python3
"""
WhatsApp Message Sender API
RESTful API для відправки повідомлень через WhatsApp Web
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import time
import os
import json
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Файл для збереження session_id
SESSION_FILE = os.path.join(os.path.dirname(__file__), '.whatsapp_session.json')
DRIVER_URL = 'http://localhost:4444/wd/hub'

app = FastAPI(
    title="WhatsApp Sender API",
    description="API для відправки повідомлень через WhatsApp Web",
    version="1.0.0"
)


class MessageRequest(BaseModel):
    contact: str = Field(..., description="Точна назва контакту/чату як відображається в WhatsApp")
    message: str = Field(..., description="Текст повідомлення для відправки")

    class Config:
        json_schema_extra = {
            "example": {
                "contact": "Іван Петренко",
                "message": "Привіт! Як справи?"
            }
        }


class MessageResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None


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
        return []


def attach_to_session(session_id, driver_url):
    """Підключається до існуючої сесії браузера"""
    from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
    from selenium.webdriver.remote.remote_connection import RemoteConnection
    from selenium.webdriver.remote.errorhandler import ErrorHandler
    from selenium.webdriver.remote.switch_to import SwitchTo
    from selenium.webdriver.remote.mobile import Mobile
    from selenium.webdriver.remote.file_detector import LocalFileDetector
    from selenium.webdriver.remote.locator_converter import LocatorConverter
    from selenium.webdriver.remote.fedcm import FedCM

    # Створюємо драйвер без ініціалізації нової сесії
    driver = object.__new__(RemoteWebDriver)
    driver.command_executor = RemoteConnection(driver_url, keep_alive=True)
    driver.session_id = session_id
    driver.w3c = True
    driver.caps = {}
    driver._is_remote = True
    driver.pinned_scripts = {}
    driver.error_handler = ErrorHandler()
    driver._switch_to = SwitchTo(driver)
    driver._mobile = Mobile(driver)
    driver.file_detector = LocalFileDetector()
    driver.locator_converter = LocatorConverter()
    driver._web_element_cls = RemoteWebDriver._web_element_cls
    driver._shadowroot_cls = RemoteWebDriver._shadowroot_cls
    driver._authenticator_id = None
    driver._fedcm = FedCM(driver)
    driver._websocket_connection = None

    # Перевіряємо чи сесія жива
    try:
        _ = driver.current_url
        return driver
    except:
        return None


def load_session_id():
    """Завантажує session_id з файлу"""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f).get('session_id')
        except:
            pass
    return None


@app.post("/send-message", response_model=MessageResponse, tags=["WhatsApp"])
async def send_message_endpoint(request: MessageRequest):
    """
    Відправляє повідомлення у WhatsApp через існуючу сесію.

    Перед використанням переконайтесь, що запущено whatsapp_session.py
    """
    # Завантажуємо збережену сесію
    saved_session_id = load_session_id()
    if not saved_session_id:
        raise HTTPException(
            status_code=400,
            detail="Немає активної сесії! Спочатку запустіть: python whatsapp_session.py"
        )

    # Перевіряємо чи сесія активна
    active_sessions = get_active_sessions(DRIVER_URL)
    if saved_session_id not in active_sessions:
        raise HTTPException(
            status_code=400,
            detail="Збережена сесія більше не активна! Запустіть заново: python whatsapp_session.py"
        )

    # Підключаємося до існуючої сесії
    driver = attach_to_session(saved_session_id, DRIVER_URL)
    if not driver:
        raise HTTPException(
            status_code=500,
            detail="Не вдалося підключитись до сесії!"
        )

    try:
        # Перевіряємо чи ми на WhatsApp Web
        if 'web.whatsapp.com' not in driver.current_url:
            driver.get('https://web.whatsapp.com')

        # Чекаємо на завантаження
        wait = WebDriverWait(driver, 30)
        try:
            wait.until(EC.presence_of_element_located((By.ID, 'pane-side')))
        except:
            raise HTTPException(
                status_code=400,
                detail="Сесія втратила авторизацію. Запустіть заново: python whatsapp_session.py"
            )

        time.sleep(1)

        # Знаходимо і відкриваємо чат
        chat_xpath = f"//span[@title='{request.contact}']"
        chat = wait.until(EC.element_to_be_clickable((By.XPATH, chat_xpath)))
        chat.click()

        # Відправляємо повідомлення
        input_xpath = "//footer//div[@contenteditable='true' and @data-tab]"
        inp = wait.until(EC.presence_of_element_located((By.XPATH, input_xpath)))
        inp.click()
        time.sleep(0.3)
        inp.send_keys(request.message + Keys.ENTER)
        time.sleep(0.5)

        return MessageResponse(
            success=True,
            message=f"Повідомлення успішно надіслано до '{request.contact}'",
            session_id=saved_session_id[:8] + "..."
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Помилка при відправці: {str(e)}"
        )


@app.get("/health", tags=["System"])
async def health_check():
    """Перевірка стану API та активної сесії"""
    saved_session_id = load_session_id()
    if not saved_session_id:
        return {
            "status": "not_ready",
            "message": "Немає активної сесії"
        }

    active_sessions = get_active_sessions(DRIVER_URL)
    is_active = saved_session_id in active_sessions

    return {
        "status": "ready" if is_active else "session_expired",
        "session_id": saved_session_id[:8] + "..." if saved_session_id else None,
        "session_active": is_active
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
