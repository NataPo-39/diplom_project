import os
import requests
from dotenv import load_dotenv

load_dotenv()


def test_speechkit():
    """Тест подключения к SpeechKit"""

    api_key = os.getenv('YANDEX_API_KEY')
    folder_id = os.getenv('YANDEX_FOLDER_ID')

    if not api_key or not folder_id:
        print("❌ Не найдены ключи SpeechKit в .env")
        return

    # Тестовый запрос к SpeechKit
    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

    headers = {
        "Authorization": f"Api-Key {api_key}",
    }

    params = {
        "folderId": folder_id,
        "lang": "ru-RU",
    }

    # Пробный запрос (без аудио, чтобы проверить доступ)
    response = requests.post(url, headers=headers, params=params)

    if response.status_code == 400:
        # 400 - ожидаемо, потому что не отправили аудио
        print("✅ SpeechKit доступен! API ключ работает.")
        print("   (Ошибка 400 - нет аудио, это нормально)")
    elif response.status_code == 403:
        print("❌ Ошибка доступа. Проверьте API ключ и folder_id")
    else:
        print(f"📡 Ответ SpeechKit: {response.status_code}")
        print(response.text[:200])


if __name__ == "__main__":
    print("🔍 Тестирую подключение к Yandex SpeechKit...")
    test_speechkit()