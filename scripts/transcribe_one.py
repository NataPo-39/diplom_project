"""
Тест транскрибации одного аудиофайла через Yandex SpeechKit.
Исправленная версия с правильными параметрами для MP3 файлов.
"""

import os
import sys
import requests
import csv
from pathlib import Path
from dotenv import load_dotenv

# Добавляем путь к проекту для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def transcribe_one_file(audio_file_path: str = None) -> None:
    """
    Транскрибирует один аудиофайл через Yandex SpeechKit.

    Args:
        audio_file_path: Путь к аудиофайлу. Если None, берёт самый маленький файл из data/input/
    """
    print("🎤 Тест транскрибации одного файла через Yandex SpeechKit")
    print("=" * 60)

    # 1. Проверяем ключи
    api_key = os.getenv('YANDEX_API_KEY')
    folder_id = os.getenv('YANDEX_FOLDER_ID')

    if not api_key:
        print("❌ Ошибка: YANDEX_API_KEY не найден в .env файле")
        print("   Добавьте в .env: YANDEX_API_KEY=ваш_ключ")
        return

    if not folder_id:
        print("❌ Ошибка: YANDEX_FOLDER_ID не найден в .env файле")
        print("   Добавьте в .env: YANDEX_FOLDER_ID=ваш_folder_id")
        return

    print(f"✅ API ключ: {api_key[:10]}...")
    print(f"✅ Folder ID: {folder_id[:10]}...")

    # 2. Находим файл для теста
    if audio_file_path is None:
        # Ищем самый маленький MP3 файл в data/input/
        input_dir = Path("data/input")
        if not input_dir.exists():
            print("❌ Папка data/input/ не существует")
            return

        mp3_files = list(input_dir.glob("*.mp3"))
        if not mp3_files:
            print("❌ В data/input/ нет MP3 файлов")
            return

        # Берём самый маленький файл для быстрого теста
        audio_file_path = min(mp3_files, key=lambda x: x.stat().st_size)
        print(f"🔍 Автовыбор: самый маленький файл - {audio_file_path.name}")

    # 3. Проверяем файл
    audio_path = Path(audio_file_path)
    if not audio_path.exists():
        print(f"❌ Файл не найден: {audio_file_path}")
        return

    file_size_kb = audio_path.stat().st_size / 1024
    print(f"📁 Файл: {audio_path.name}")
    print(f"📊 Размер: {file_size_kb:.1f} KB")
    print(f"📍 Путь: {audio_path}")

    # 4. Читаем файл
    try:
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        print(f"✅ Файл прочитан: {len(audio_data)} байт")
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return

    # 5. Подготавливаем запрос к SpeechKit
    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

    headers = {
        "Authorization": f"Api-Key {api_key}",
        # Для MP3 можно указать Content-Type, но не обязательно
        # SpeechKit сам определит формат по содержимому
    }

    # ВАЖНО: Правильные параметры для SpeechKit
    # SpeechKit принимает MP3, но без указания формата или с format='lpcm'
    params = {
        "folderId": folder_id,
        "lang": "ru-RU",
        # НЕ указываем format для MP3 - SpeechKit сам определит
        # "sampleRateHertz": "8000",  # Опционально, можно указать частоту
        # "profanityFilter": "true",   # Опционально: фильтр ненормативной лексики
    }

    print(f"\n🚀 Отправляю запрос с параметрами: {params}")

    # 6. Отправляем запрос
    try:
        response = requests.post(
            url,
            headers=headers,
            params=params,
            data=audio_data,
            timeout=30
        )

        print(f"📡 Статус ответа: {response.status_code}")

        # 7. Обрабатываем ответ
        if response.status_code == 200:
            result = response.json()

            if "result" in result:
                text = result["result"]
                print(f"\n🎉 УСПЕХ! Транскрибация выполнена!")
                print("=" * 40)
                print(f"📝 ТЕКСТ ({len(text)} символов):")
                print("-" * 40)
                print(text)
                print("-" * 40)

                # Сохраняем результат в файл
                output_dir = Path("data/output")
                output_dir.mkdir(exist_ok=True)

                output_file = output_dir / f"transcript_{audio_path.stem}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)

                print(f"\n💾 Результат сохранён в: {output_file}")

                # Также сохраняем в общий файл
                csv_file = output_dir / "transcripts.csv"
                file_exists = csv_file.exists()

                with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(['filename', 'size_kb', 'transcript'])
                    writer.writerow([audio_path.name, f"{file_size_kb:.1f}", text])

                print(f"📋 Добавлено в CSV: {csv_file}")

            else:
                print(f"❌ Ошибка в ответе SpeechKit: {result}")
                if "error_code" in result:
                    print(f"   Код ошибки: {result['error_code']}")
                if "error_message" in result:
                    print(f"   Сообщение: {result['error_message']}")

        elif response.status_code == 403:
            print("❌ Ошибка 403: Доступ запрещён")
            print("   Проверьте:")
            print("   1. Правильность API ключа")
            print("   2. Активен ли API ключ")
            print("   3. Есть ли доступ у сервисного аккаунта к SpeechKit")
            print(f"   Ответ: {response.text[:200]}")

        elif response.status_code == 400:
            print("❌ Ошибка 400: Неверный запрос")
            print("   Возможные причины:")
            print("   1. Неподдерживаемый формат аудио")
            print("   2. Слишком большой файл (>200MB)")
            print("   3. Слишком длинное аудио (>30 минут)")
            print("   4. Неверные параметры запроса")
            print("   5. Проблемы с кодировкой аудио")
            print(f"   Полный ответ: {response.text}")

        elif response.status_code == 402:
            print("❌ Ошибка 402: Недостаточно средств")
            print("   Пополните баланс в Yandex Cloud Console")
            print(f"   Ответ: {response.text[:200]}")

        elif response.status_code == 429:
            print("❌ Ошибка 429: Слишком много запросов")
            print("   Превышена квота. Подождите или увеличьте лимиты")
            print(f"   Ответ: {response.text[:200]}")

        else:
            print(f"❌ Неизвестная ошибка: {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")

    except requests.exceptions.Timeout:
        print("❌ Таймаут: SpeechKit не ответил за 30 секунд")
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка соединения: не удалось подключиться к SpeechKit")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")


def test_different_formats():
    """Тестирует разные параметры для поиска рабочего варианта"""
    print("\n🔧 Тестирование разных параметров SpeechKit")
    print("=" * 60)

    api_key = os.getenv('YANDEX_API_KEY')
    folder_id = os.getenv('YANDEX_FOLDER_ID')

    # Берём тестовый файл
    test_file = Path("data/input/1350033465.mp3")
    if not test_file.exists():
        print(f"❌ Тестовый файл не найден: {test_file}")
        return

    with open(test_file, 'rb') as f:
        audio_data = f.read()

    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    headers = {"Authorization": f"Api-Key {api_key}"}

    # Тестируем разные варианты параметров
    test_cases = [
        {"name": "Без параметров", "params": {"folderId": folder_id, "lang": "ru-RU"}},
        {"name": "С частотой 8000", "params": {"folderId": folder_id, "lang": "ru-RU", "sampleRateHertz": "8000"}},
        {"name": "С форматом lpcm", "params": {"folderId": folder_id, "lang": "ru-RU", "format": "lpcm"}},
        {"name": "С форматом oggopus", "params": {"folderId": folder_id, "lang": "ru-RU", "format": "oggopus"}},
        {"name": "MP3 с Content-Type", "params": {"folderId": folder_id, "lang": "ru-RU"},
         "headers": {"Authorization": f"Api-Key {api_key}", "Content-Type": "audio/mpeg"}},
    ]

    for test in test_cases:
        print(f"\n🔍 Тест: {test['name']}")
        print(f"   Параметры: {test['params']}")

        try:
            current_headers = test.get('headers', headers)
            response = requests.post(url, headers=current_headers,
                                    params=test['params'], data=audio_data, timeout=15)

            print(f"   Статус: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                text = result.get("result", "Нет результата")
                print(f"   ✅ УСПЕХ! Текст: {text[:80]}...")
                return test['params']  # Возвращаем рабочие параметры
            else:
                print(f"   ❌ Ошибка: {response.text[:100]}")

        except Exception as e:
            print(f"   ❌ Исключение: {e}")

    return None


def find_smallest_mp3():
    """Находит самый маленький MP3 файл в data/input/"""
    input_dir = Path("data/input")
    if not input_dir.exists():
        return None

    mp3_files = list(input_dir.glob("*.mp3"))
    if not mp3_files:
        return None

    return min(mp3_files, key=lambda x: x.stat().st_size)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🔧 ТЕСТ ТРАНСКРИБАЦИИ ОДНОГО ФАЙЛА (ИСПРАВЛЕННАЯ ВЕРСИЯ)")
    print("=" * 60)

    # Сначала тестируем разные параметры
    print("\n📊 Поиск рабочих параметров...")
    working_params = test_different_formats()

    if working_params:
        print(f"\n🎯 Найдены рабочие параметры: {working_params}")
        print("   Теперь пробуем основную транскрибацию...")
    else:
        print("\n⚠️  Не удалось найти рабочие параметры.")
        print("   Пробуем стандартный вариант...")

    # Запускаем основную транскрибацию
    smallest = find_smallest_mp3()
    if smallest:
        print(f"\n🎯 Будет использован самый маленький файл: {smallest.name}")
        transcribe_one_file(str(smallest))
    else:
        print("❌ Не найдены MP3 файлы в data/input/")

    print("\n" + "=" * 60)
    print("📋 ИНСТРУКЦИЯ ПО ДАЛЬНЕЙШИМ ДЕЙСТВИЯМ:")
    print("=" * 60)
    print("✅ Если транскрибация успешна:")
    print("   1. Результат сохранён в data/output/")
    print("   2. Можно переходить к обработке всех файлов")
    print("   3. Следующий шаг: создание основного пайплайна")
    print()
    print("❌ Если есть ошибки:")
    print("   1. Проверьте баланс в Yandex Cloud (должен быть > 1 рубля)")
    print("   2. Убедитесь, что SpeechKit API активирован")
    print("   3. Проверьте аудиофайл - возможно, он повреждён")
    print("   4. Попробуйте другой файл из data/input/")