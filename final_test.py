"""
final_test.py - окончательный тест с обработкой
"""
import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range, low_pass_filter, high_pass_filter

# ======================== НАСТРОЙКА ========================
os.environ["PATH"] = r"C:\ffmpeg\bin;" + os.environ["PATH"]
AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"

load_dotenv()
API_KEY = os.getenv('YANDEX_API_KEY')
FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')


# ===========================================================

def improve_audio_quality(audio: AudioSegment) -> AudioSegment:
    """Улучшает качество аудио для лучшего распознавания"""
    print("🔧 Улучшение качества аудио...")

    processed = audio

    # 1. Конвертация в моно (если нужно)
    if processed.channels > 1:
        processed = processed.set_channels(1)
        print("   ✅ Конвертирован в моно")

    # 2. Установка частоты 16000 Hz
    if processed.frame_rate != 16000:
        processed = processed.set_frame_rate(16000)
        print("   ✅ Частота: 16000 Hz")

    # 3. ФИЛЬТРЫ ДЛЯ ТЕЛЕФОННОЙ РЕЧИ
    # Низкочастотный фильтр (убирает высокие шумы)
    processed = low_pass_filter(processed, 3000)  # Оставляем до 3000 Hz
    print("   ✅ Низкочастотный фильтр (до 3000 Hz)")

    # Высокочастотный фильтр (убирает низкочастотный гул)
    processed = high_pass_filter(processed, 300)  # Убираем ниже 300 Hz
    print("   ✅ Высокочастотный фильтр (от 300 Hz)")

    # 4. УСИЛЕНИЕ СРЕДНИХ ЧАСТОТ (где речь)
    # Создаём эквалайзер: усиление 100-3000 Hz
    processed = processed.apply_gain(6)  # Усиление на 6 dB
    print("   ✅ Усиление речи (+6 dB)")

    # 5. Нормализация
    processed = normalize(processed)
    print(f"   ✅ Громкость: {processed.dBFS:.1f} dBFS")

    # 6. Компрессия
    processed = compress_dynamic_range(processed)
    print("   ✅ Динамический диапазон сжат")

    return processed


def test_with_speechkit(audio_data: bytes, params: dict, label: str):
    """Тестирует аудио с SpeechKit"""
    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    headers = {"Authorization": f"Api-Key {API_KEY}"}

    print(f"\n🎤 Тест '{label}':")
    print(f"   ⚙️  Параметры: {params}")

    response = requests.post(
        url,
        headers=headers,
        params=params,
        data=audio_data,
        timeout=30
    )

    print(f"   📡 Статус: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        text = result.get("result", "")

        if text:
            print(f"   🎉 УСПЕХ! Текст ({len(text)} символов):")
            print(f"   '{text[:100]}...'" if len(text) > 100 else f"   '{text}'")
            return text
        else:
            print(f"   ⚠️  Пустой текст")
            return ""
    else:
        print(f"   ❌ Ошибка: {response.text[:100]}")
        return None


def main():
    print("=" * 70)
    print("🎯 ОКОНЧАТЕЛЬНЫЙ ТЕСТ ОБРАБОТКИ АУДИО")
    print("=" * 70)

    # Исходный файл
    input_file = Path("data/input/1350033465.mp3")

    if not input_file.exists():
        print(f"❌ Файл не найден: {input_file}")
        return

    # 1. Загружаем исходный файл
    print(f"📥 Загрузка: {input_file.name}")
    original_audio = AudioSegment.from_file(str(input_file))

    print(f"📊 Исходные параметры:")
    print(f"   • Длительность: {len(original_audio) / 1000:.2f} сек")
    print(f"   • Частота: {original_audio.frame_rate} Hz")
    print(f"   • Громкость: {original_audio.dBFS:.1f} dBFS")

    # 2. Тестируем исходный файл (как было)
    with open(input_file, 'rb') as f:
        original_data = f.read()

    # Тест 1: Исходный файл
    params_original = {
        "folderId": FOLDER_ID,
        "lang": "ru-RU",
        "format": "lpcm",
        "sampleRateHertz": "8000",  # Исходная частота
    }

    result_original = test_with_speechkit(original_data, params_original, "Исходный файл")

    # 3. Улучшаем качество
    print(f"\n{'=' * 50}")
    improved_audio = improve_audio_quality(original_audio)

    print(f"\n📊 Улучшенные параметры:")
    print(f"   • Длительность: {len(improved_audio) / 1000:.2f} сек")
    print(f"   • Частота: {improved_audio.frame_rate} Hz")
    print(f"   • Громкость: {improved_audio.dBFS:.1f} dBFS")

    # Сохраняем улучшенный файл
    improved_path = Path("data/processed/improved_1350033465.wav")
    improved_audio.export(
        str(improved_path),
        format="wav",
        parameters=["-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le"]
    )

    # 4. Тестируем улучшенный файл
    with open(improved_path, 'rb') as f:
        improved_data = f.read()

    # Тест 2: Улучшенный файл
    params_improved = {
        "folderId": FOLDER_ID,
        "lang": "ru-RU",
        "format": "lpcm",
        "sampleRateHertz": "16000",  # Новая частота
    }

    result_improved = test_with_speechkit(improved_data, params_improved, "Улучшенный файл")

    # 5. Тест 3: Экспериментальные параметры
    print(f"\n{'=' * 50}")
    print("🧪 ЭКСПЕРИМЕНТАЛЬНЫЕ ПАРАМЕТРЫ:")

    experimental_params = [
        {"format": "oggopus", "sampleRateHertz": "16000"},
        {"format": "lpcm", "sampleRateHertz": "8000", "model": "general:rc"},  # Разговорная модель
        {"format": "lpcm", "sampleRateHertz": "16000", "profanityFilter": "false"},
    ]

    for i, params in enumerate(experimental_params, 1):
        full_params = {"folderId": FOLDER_ID, "lang": "ru-RU", **params}
        test_with_speechkit(improved_data, full_params, f"Эксперимент {i}")

    # 6. ИТОГ
    print(f"\n{'=' * 70}")
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"{'=' * 70}")

    if result_improved:
        print(f"✅ УСПЕХ! SpeechKit распознал речь после обработки")
        print(f"📝 Текст: {result_improved[:50]}...")

        # Сохраняем результат
        output_dir = Path("data/output")
        output_dir.mkdir(exist_ok=True)

        with open(output_dir / "final_result.txt", 'w', encoding='utf-8') as f:
            f.write(f"Файл: {input_file.name}\n")
            f.write(f"Исходный результат: {result_original if result_original else 'пусто'}\n")
            f.write(f"Улучшенный результат: {result_improved}\n")

        print(f"💾 Результат сохранён: data/output/final_result.txt")

    elif result_original:
        print(f"⚠️  Исходный файл распознался: {result_original[:50]}...")

    else:
        print(f"❌ SpeechKit не распознал речь даже после обработки")
        print(f"\n💡 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
        print(f"   1. Очень плохое качество записи")
        print(f"   2. SpeechKit не поддерживает такой тип речи")
        print(f"   3. Нужна другая модель распознавания")
        print(f"   4. Возможно, речь на другом языке")

    print(f"\n📁 Созданные файлы:")
    print(f"   • {input_file.name} (исходный)")
    print(f"   • {improved_path.name} (улучшенный, {improved_path.stat().st_size / 1024:.1f} KB)")

    print(f"\n🎧 Проверьте улучшенный файл:")
    print(f"   📍 {improved_path.absolute()}")
    print(f"   🔊 Откройте в аудиоплеере, сравните с оригиналом")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback

        traceback.print_exc()

    input("\nНажмите Enter для выхода...")
