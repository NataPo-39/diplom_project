"""
config.py - Загрузка конфигурации из .env файла
Используется во всех модулях проекта для доступа к настройкам
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Определяем путь к корню проекта (где лежит .env файл)
# Поднимаемся на 2 уровня вверх из part2/src/utils/
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"


def load_config():
    """
    Загружает конфигурацию из .env файла

    Возвращает:
        dict: Словарь с настройками
    """
    # Загружаем переменные из .env
    load_dotenv(dotenv_path=ENV_PATH)

    # Проверяем обязательные переменные
    required_vars = ['YANDEX_API_KEY', 'YANDEX_FOLDER_ID']
    config = {}
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            config[var.lower()] = value
        else:
            missing_vars.append(var)

    # Если есть пропущенные переменные - сообщаем об ошибке
    if missing_vars:
        raise ValueError(
            f"Отсутствуют обязательные переменные в .env файле: {', '.join(missing_vars)}\n"
            f"Убедитесь, что файл .env находится в корне проекта и содержит эти переменные."
        )

    # Добавляем необязательные переменные
    optional_vars = {
        'YANDEX_GPT_MODEL': 'yandexgpt-latest',  # Модель по умолчанию
        'ASSISTANT_NAME': 'Cult Constructions Assistant',
        'LOG_LEVEL': 'INFO'
    }

    for var, default in optional_vars.items():
        config[var.lower()] = os.getenv(var, default)

    print(f"✅ Конфигурация загружена из: {ENV_PATH}")
    print(f"📁 Folder ID: {config.get('yandex_folder_id', 'не задан')[:10]}...")
    print(f"🔑 API Key длина: {len(config.get('yandex_api_key', ''))} символов")

    return config


# Глобальный объект конфигурации для импорта в других модулях
config = load_config()

# Пример использования в других файлах:
# from src.utils.config import config
# api_key = config['yandex_api_key']
# folder_id = config['yandex_folder_id']