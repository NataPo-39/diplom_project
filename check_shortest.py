"""
check_shortest.py - находит самый короткий файл
"""
from pathlib import Path
from pydub import AudioSegment
import os

# Установите пути к FFmpeg
os.environ["PATH"] = r"C:\ffmpeg\bin;" + os.environ["PATH"]
AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"


def find_shortest_file():
    """Находит самый короткий MP3 файл"""
    input_dir = Path("data/input")

    if not input_dir.exists():
        print("❌ Папка data/input не существует")
        return

    mp3_files = list(input_dir.glob("*.mp3"))

    if not mp3_files:
        print("❌ MP3 файлы не найдены")
        return

    print("=" * 60)
    print("🔍 ПОИСК САМОГО КОРОТКОГО ФАЙЛА")
    print("=" * 60)

    file_durations = []

    for file_path in mp3_files:
        try:
            audio = AudioSegment.from_file(str(file_path))
            duration_sec = len(audio) / 1000
            file_durations.append((file_path, duration_sec))

            print(f"{file_path.name:20} → {duration_sec:6.2f} секунд")

        except Exception as e:
            print(f"{file_path.name:20} → ОШИБКА: {e}")

    if file_durations:
        # Сортируем по длительности
        file_durations.sort(key=lambda x: x[1])

        shortest = file_durations[0]
        print("\n" + "=" * 60)
        print(f"🎯 САМЫЙ КОРОТКИЙ ФАЙЛ:")
        print(f"📁 {shortest[0].name}")
        print(f"⏱️  {shortest[1]:.2f} секунд ({shortest[1] / 60:.2f} минут)")

        # Проверяем, меньше ли 30 секунд
        if shortest[1] <= 30:
            print(f"✅ Меньше 30 секунд - можно тестировать")
        else:
            print(f"⚠️  Больше 30 секунд - нужно разделять")

        return shortest[0]

    return None


def test_short_file_transcription(file_path: Path):
    """Тестирует транскрибацию короткого файла"""
    print("\n" + "=" * 60)
    print(f"🎤 ТЕСТ ТРАНСКРИБАЦИИ: {file_path.name}")
    print("=" * 60)

    try:
        import requests
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.getenv('YANDEX_API_KEY')
        folder_id = os.getenv('YANDEX_FOLDER_ID')

        if not api_key or not folder_id:
            print("❌ Не найдены ключи в .env файле")
            return

        # Читаем файл напрямую (без обработки для теста)
        with open(file_path, 'rb') as f:
            audio_data = f.read()

        url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        headers = {"Authorization": f"Api-Key {api_key}"}

        # Параметры для MP3 файла
        params = {
            "folderId": folder_id,
            "lang": "ru-RU",
            "format": "lpcm",
            "sampleRateHertz": "8000",  # Исходная частота файлов
        }

        print(f"📤 Отправляю файл {file_path.name} ({len(audio_data) / 1024:.1f} KB)")
        print(f"⚙️  Параметры: {params}")

        response = requests.post(
            url,
            headers=headers,
            params=params,
            data=audio_data,
            timeout=30
        )

        print(f"📡 Статус: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            text = result.get("result", "")

            if text:
                print(f"\n🎉 УСПЕХ! Текст ({len(text)} символов):")
                print("-" * 50)
                print(text)
                print("-" * 50)
            else:
                print(f"\n⚠️  SpeechKit вернул пустой текст")
                print("   Возможные причины:")
                print("   1. В файле действительно нет речи")
                print("   2. Речь слишком тихая")
                print("   3. Неправильные параметры")
        else:
            print(f"\n❌ Ошибка: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Ошибка транскрибации: {e}")


if __name__ == "__main__":
    shortest_file = find_shortest_file()

    if shortest_file:
        answer = input("\n🧪 Протестировать этот файл через SpeechKit? (да/НЕТ): ")

        if answer.lower() == 'да':
            test_short_file_transcription(shortest_file)
        else:
            print("❌ Тест отменён")

    input("\nНажмите Enter для выхода...")