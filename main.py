"""
main.py - Основной скрипт системы транскрибации звонков
Обновлённая версия с предобработкой аудио
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Добавляем ffmpeg в PATH для Windows (исправление для PyCharm/PowerShell)
ffmpeg_path = r"C:\ffmpeg\bin"
if ffmpeg_path not in os.environ["PATH"]:
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]
    print(f"✅ Добавлен ffmpeg в PATH: {ffmpeg_path}")

# Добавляем путь к src в sys.path для импорта модулей
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Импорт наших модулей
try:
    from services.audio_processor_fixed import AudioProcessorFixed as AudioProcessor

    print("✅ Модуль audio_processor_final загружен")
except ImportError as e:
    print(f"❌ Ошибка импорта audio_processor_final: {e}")
    print("   Убедитесь, что файл существует в src/services/")
    sys.exit(1)


def setup_environment():
    """Настройка окружения и проверка зависимостей"""
    print("=" * 70)
    print("🎯 СИСТЕМА ТРАНСКРИБАЦИИ ТЕЛЕФОННЫХ ЗВОНКОВ")
    print("=" * 70)

    # Загружаем переменные окружения
    load_dotenv()

    # Проверяем обязательные переменные
    required_vars = ['YANDEX_API_KEY', 'YANDEX_FOLDER_ID']
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Ошибка: Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        print(f"   Заполните файл .env на основе .env.example")
        return False

    print("✅ Переменные окружения загружены")

    # Проверяем структуру папок
    required_folders = ['data/input', 'data/processed', 'data/output', 'data/logs']

    for folder in required_folders:
        folder_path = Path(folder)
        if not folder_path.exists():
            print(f"📁 Создаю папку: {folder}")
            folder_path.mkdir(parents=True, exist_ok=True)

    print("✅ Структура папок проверена")
    return True


def analyze_input_files():
    """Анализирует файлы во входной папке"""
    print("\n" + "=" * 70)
    print("📁 АНАЛИЗ ВХОДНЫХ ФАЙЛОВ")
    print("=" * 70)

    input_dir = Path("data/input")

    if not input_dir.exists():
        print("❌ Папка data/input/ не существует")
        return []

    mp3_files = list(input_dir.glob("*.mp3"))

    if not mp3_files:
        print("❌ В папке data/input/ нет MP3 файлов")
        print("   Поместите MP3 файлы в папку data/input/")
        return []

    print(f"✅ Найдено MP3 файлов: {len(mp3_files)}")

    # Выводим информацию о файлах
    total_size_mb = sum(f.stat().st_size for f in mp3_files) / (1024 * 1024)
    print(f"📊 Общий размер: {total_size_mb:.2f} MB")
    print(f"📊 Средний размер файла: {total_size_mb / len(mp3_files):.2f} MB")

    print("\n📋 Список файлов:")
    for i, file_path in enumerate(mp3_files[:10], 1):  # Показываем первые 10
        size_kb = file_path.stat().st_size / 1024
        print(f"{i:2d}. {file_path.name:30} {size_kb:7.1f} KB")

    if len(mp3_files) > 10:
        print(f"   ... и ещё {len(mp3_files) - 10} файлов")

    return mp3_files


def process_single_file(file_path: Path, processor: AudioProcessor, test_transcription: bool = True):
    """Обрабатывает один файл"""
    print(f"\n{'=' * 70}")
    print(f"🔧 ОБРАБОТКА: {file_path.name}")
    print(f"{'=' * 70}")

    # Обработка аудио
    success, message, processed_path = processor.process_file(file_path)

    if not success:
        print(f"❌ Ошибка обработки: {message}")
        return False, None

    if not processed_path or not processed_path.exists():
        print(f"❌ Обработанный файл не создан")
        return False, None

    print(f"✅ Файл обработан: {processed_path.name}")

    # Тестируем транскрибацию, если нужно
    if test_transcription:
        transcription_result = test_speechkit_transcription(processed_path)

        if transcription_result:
            text, params = transcription_result
            if text:
                print(f"🎉 УСПЕХ! SpeechKit распознал текст ({len(text)} символов)")
                print(f"📋 Параметры: {params}")

                # Сохраняем транскрипцию
                save_transcription(file_path, text, params)
                return True, text
            else:
                print(f"⚠️  SpeechKit вернул пустой текст")
                print(f"   Возможно, в файле нет речи или она неразборчива")
                return False, None
        else:
            print(f"❌ Ошибка транскрибации")
            return False, None

    return True, None


def test_speechkit_transcription(audio_path: Path):
    """Тестирует транскрибацию через SpeechKit"""
    print(f"\n🎤 ТЕСТИРУЮ ТРАНСКРИБАЦИЮ...")

    try:
        import requests
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.getenv('YANDEX_API_KEY')
        folder_id = os.getenv('YANDEX_FOLDER_ID')

        if not api_key or not folder_id:
            print("❌ Не найдены ключи в .env файле")
            return None

        # Читаем обработанный файл
        with open(audio_path, 'rb') as f:
            audio_data = f.read()

        url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        headers = {"Authorization": f"Api-Key {api_key}"}

        # Оптимальные параметры для обработанного файла
        params = {
            "folderId": folder_id,
            "lang": "ru-RU",
            "format": "lpcm",
            "sampleRateHertz": "16000",
        }

        response = requests.post(
            url,
            headers=headers,
            params=params,
            data=audio_data,
            timeout=30
        )

        print(f"📡 Статус SpeechKit: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            text = result.get("result", "")
            return text, params
        else:
            print(f"❌ Ошибка SpeechKit: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"❌ Ошибка транскрибации: {e}")
        return None


def save_transcription(original_file: Path, text: str, params: dict):
    """Сохраняет результат транскрибации"""
    output_dir = Path("data/output")
    output_dir.mkdir(exist_ok=True)

    # Сохраняем как текст
    text_file = output_dir / f"transcript_{original_file.stem}.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(f"Файл: {original_file.name}\n")
        f.write(f"Дата обработки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Параметры: {params}\n")
        f.write(f"\nТЕКСТ ТРАНСКРИБАЦИИ:\n")
        f.write("=" * 50 + "\n")
        f.write(text)
        f.write("\n" + "=" * 50)

    print(f"💾 Транскрипция сохранена: {text_file.name}")

    # Добавляем в CSV файл
    csv_file = output_dir / "all_transcriptions.csv"
    file_exists = csv_file.exists()

    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        import csv
        writer = csv.writer(f)
        if not file_exists:
            # Заголовки
            writer.writerow([
                'filename', 'date', 'duration_sec',
                'text_length', 'parameters', 'transcription'
            ])

        # Предполагаемая длительность (нужно будет добавить реальную)
        duration = 0  # Можно получить из аудиофайла

        writer.writerow([
            original_file.name,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            duration,
            len(text),
            str(params),
            text[:100] + "..." if len(text) > 100 else text
        ])

    print(f"📊 Добавлено в CSV: {csv_file.name}")


def process_all_files(mp3_files, test_first_only: bool = True):
    """Обрабатывает все файлы"""
    print("\n" + "=" * 70)
    print("🔄 ЗАПУСК ОБРАБОТКИ ВСЕХ ФАЙЛОВ")
    print("=" * 70)

    processor = AudioProcessor()

    success_count = 0
    error_count = 0

    if test_first_only and mp3_files:
        print("🔬 ТЕСТОВЫЙ РЕЖИМ: обрабатываю только первый файл")
        files_to_process = [mp3_files[0]]
    else:
        print(f"⚙️  РЕЖИМ ПАКЕТНОЙ ОБРАБОТКИ: {len(mp3_files)} файлов")
        files_to_process = mp3_files

    for i, file_path in enumerate(files_to_process, 1):
        print(f"\n📁 Файл {i}/{len(files_to_process)}")

        success, text = process_single_file(
            file_path,
            processor,
            test_transcription=True
        )

        if success:
            success_count += 1
        else:
            error_count += 1

        # Небольшая пауза между файлами
        if i < len(files_to_process):
            print(f"\n⏱️  Пауза 2 секунды перед следующим файлом...")
            import time
            time.sleep(2)

    return success_count, error_count


def main():
    """Основная функция"""

    # Настройка окружения
    if not setup_environment():
        return

    # Анализ входных файлов
    mp3_files = analyze_input_files()

    if not mp3_files:
        print("\n❌ Нет файлов для обработки")
        return

    # Обработка файлов
    success_count, error_count = process_all_files(
        mp3_files,
        test_first_only=True  # Сначала тестируем только первый файл
    )

    # Итог
    print("\n" + "=" * 70)
    print("📊 ИТОГИ ОБРАБОТКИ")
    print("=" * 70)
    print(f"✅ Успешно обработано: {success_count}")
    print(f"❌ Ошибок: {error_count}")
    print(f"📁 Всего файлов: {len(mp3_files)}")

    if success_count > 0:
        print(f"\n🎉 ОБРАБОТКА УСПЕШНА!")
        print(f"📂 Обработанные файлы в: data/processed/")
        print(f"📝 Транскрипции в: data/output/")

        # Показываем пример транскрипции
        output_dir = Path("data/output")
        text_files = list(output_dir.glob("transcript_*.txt"))

        if text_files:
            print(f"\n📄 Пример транскрипции из {text_files[0].name}:")
            with open(text_files[0], 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-10:]:  # Последние 10 строк
                    print(f"   {line.rstrip()}")
    else:
        print(f"\n⚠️  НИ ОДИН ФАЙЛ НЕ ОБРАБОТАН УСПЕШНО")
        print(f"   Проверьте:")
        print(f"   1. Качество аудиофайлов")
        print(f"   2. Ключи в .env файле")
        print(f"   3. Подключение к интернету")

    print("\n" + "=" * 70)
    print("🏁 ОБРАБОТКА ЗАВЕРШЕНА")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Обработка прервана пользователем")
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()

    # Пауза перед закрытием (только для Windows)
    if os.name == 'nt':
        input("\nНажмите Enter для выхода...")