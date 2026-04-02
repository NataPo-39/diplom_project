import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def test_file(file_path: Path):
    """Тестирует один файл"""

    api_key = os.getenv('YANDEX_API_KEY')
    folder_id = os.getenv('YANDEX_FOLDER_ID')

    with open(file_path, 'rb') as f:
        audio_data = f.read()

    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    headers = {"Authorization": f"Api-Key {api_key}"}

    # Тестируем разные параметры
    test_params = [
        {"format": "lpcm", "sampleRateHertz": "8000"},
        {"format": "lpcm", "sampleRateHertz": "16000"},
        {"format": "oggopus", "sampleRateHertz": "8000"},
    ]

    for params in test_params:
        full_params = {
            "folderId": folder_id,
            "lang": "ru-RU",
            **params
        }

        try:
            response = requests.post(url, headers=headers,
                                     params=full_params, data=audio_data, timeout=20)

            if response.status_code == 200:
                result = response.json()
                text = result.get("result", "")

                if text:
                    return True, text, full_params

        except Exception:
            continue

    return False, "", {}


def main():
    print("🔍 Тестирование нескольких файлов")
    print("=" * 60)

    input_dir = Path("data/input")
    files = list(input_dir.glob("*.mp3"))

    # Сортируем по размеру (от маленьких к большим)
    files.sort(key=lambda x: x.stat().st_size)

    for i, file_path in enumerate(files[:5]):  # Первые 5 файлов
        print(f"\n{i + 1}. Тестирую: {file_path.name} ({file_path.stat().st_size / 1024:.1f} KB)")

        success, text, params = test_file(file_path)

        if success:
            print(f"   ✅ УСПЕХ! Параметры: {params}")
            print(f"   📝 Текст ({len(text)} символов): {text[:100]}...")

            # Сохраняем результат
            output_dir = Path("data/output")
            output_dir.mkdir(exist_ok=True)

            with open(output_dir / f"GOOD_{file_path.stem}.txt", 'w', encoding='utf-8') as f:
                f.write(f"Файл: {file_path.name}\n")
                f.write(f"Параметры: {params}\n")
                f.write(f"Текст ({len(text)} символов):\n")
                f.write(text)

            print(f"   💾 Сохранено: data/output/GOOD_{file_path.stem}.txt")
            break  # Останавливаемся на первом успешном
        else:
            print(f"   ❌ Не распознано (пустой результат)")

    print("\n" + "=" * 60)
    if success:
        print("🎉 НАЙДЕН РАБОЧИЙ ФАЙЛ!")
        print(f"📁 Файл: {file_path.name}")
        print(f"⚙️  Параметры: {params}")
    else:
        print("⚠️  Ни один файл не распознан")
        print("   Возможные причины:")
        print("   1. Все файлы действительно без речи")
        print("   2. Неправильная частота дискретизации")
        print("   3. SpeechKit не поддерживает такой формат MP3")


if __name__ == "__main__":
    main()