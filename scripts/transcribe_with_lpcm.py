"""
Транскрибация с рабочими параметрами: format='lpcm'
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def transcribe_with_lpcm():
    """Транскрибация с format='lpcm' (рабочие параметры!)"""

    api_key = os.getenv('YANDEX_API_KEY')
    folder_id = os.getenv('YANDEX_FOLDER_ID')

    # Берём тестовый файл
    test_file = Path("data/input/1350033465.mp3")

    print("🎤 ТРАНСКРИБАЦИЯ С format='lpcm' (РАБОЧИЕ ПАРАМЕТРЫ)")
    print("=" * 60)

    with open(test_file, 'rb') as f:
        audio_data = f.read()

    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

    headers = {
        "Authorization": f"Api-Key {api_key}",
    }

    # РАБОЧИЕ ПАРАМЕТРЫ из теста
    params = {
        "folderId": folder_id,
        "lang": "ru-RU",
        "format": "lpcm",  # ← КЛЮЧЕВОЙ ПАРАМЕТР
        # "sampleRateHertz": "8000",  # можно попробовать добавить
    }

    print(f"📤 Отправляю файл: {test_file.name} ({len(audio_data)} байт)")
    print(f"📋 Параметры: {params}")

    try:
        response = requests.post(
            url,
            headers=headers,
            params=params,
            data=audio_data,
            timeout=30
        )

        print(f"📡 Ответ: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            text = result.get("result", "")

            print(f"\n🎉 УСПЕХ! Текст ({len(text)} символов):")
            print("-" * 40)
            print(text)
            print("-" * 40)

            # Сохраняем
            output_dir = Path("data/output")
            output_dir.mkdir(exist_ok=True)

            # Сохраняем как текст
            with open(output_dir / f"transcript_{test_file.stem}.txt", 'w', encoding='utf-8') as f:
                f.write(text)

            print(f"💾 Сохранено: data/output/transcript_{test_file.stem}.txt")

            # И в CSV
            import csv
            csv_file = output_dir / "transcripts.csv"
            file_size_kb = len(audio_data) / 1024

            file_exists = csv_file.exists()
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['filename', 'size_kb', 'transcript'])
                writer.writerow([test_file.name, f"{file_size_kb:.1f}", text])

            print(f"📊 Добавлено в CSV: transcripts.csv")

        else:
            print(f"❌ Ошибка: {response.text}")

    except Exception as e:
        print(f"❌ Исключение: {e}")


if __name__ == "__main__":
    transcribe_with_lpcm()