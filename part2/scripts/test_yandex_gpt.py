"""
test_yandex_gpt.py - Тестирование подключения к Yandex GPT API
Использует правильный model_uri из AI Studio
"""

import sys
from pathlib import Path

# Настраиваем пути
PART2_ROOT = Path(__file__).parent.parent.absolute()
SRC_PATH = PART2_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

try:
    from utils.config import config

    print("✅ Модуль config успешно импортирован")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

import requests
import json


def test_yandex_gpt_connection():
    """
    Тестирует подключение к Yandex GPT API
    """
    print("🧪 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К YANDEX GPT")
    print("=" * 60)

    # Получаем конфигурацию
    api_key = config.get('yandex_api_key')
    folder_id = config.get('yandex_folder_id')

    if not api_key or not folder_id:
        print("❌ Ошибка: API ключ или folder_id не найдены")
        return False

    # ВАЖНО: Используем точный URI из AI Studio
    model_uri = "gpt://b1gtp8bn97gg21fl5e9j/yandexgpt-5.1/latest"

    print(f"📁 Folder ID: {folder_id[:10]}...")
    print(f"🔑 API Key длина: {len(api_key)} символов")
    print(f"🤖 Model URI: {model_uri}")

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "modelUri": model_uri,  # ИСПРАВЛЕНО: теперь modelUri, не modelUrl
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": "50"
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты - тестовый помощник. Отвечай кратко на русском языке одним предложением."
            },
            {
                "role": "user",
                "text": "Привет! Как дела? Ответь очень кратко."
            }
        ]
    }

    try:
        print("\n🔄 Отправляю запрос к Yandex GPT API...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"📡 Статус ответа: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            alternatives = result.get("result", {}).get("alternatives", [])

            if alternatives:
                answer = alternatives[0].get("message", {}).get("text", "")
                if answer:
                    print(f"\n✅ УСПЕХ! Подключение работает!")
                    print(f"💬 Ответ модели: {answer}")
                    return True
                else:
                    print("⚠️ Ответ пустой")
            else:
                print("⚠️ Нет альтернатив в ответе")
        else:
            print(f"❌ Ошибка HTTP {response.status_code}")
            print(f"   Текст ошибки: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

    return False


def main():
    print("🎯 ТЕСТ YANDEX GPT API")
    print("=" * 60)
    success = test_yandex_gpt_connection()
    print("\n" + "=" * 60)
    if success:
        print("✅ ТЕСТ ПРОЙДЕН УСПЕШНО!")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН")


if __name__ == "__main__":
    main()
    input("\nНажмите Enter для выхода...")