"""
audio_processor_final.py - окончательная версия обработчика аудио
"""
import os
from pathlib import Path
from typing import Optional, Tuple
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range

# ======================== ИСПРАВЛЕНИЕ ДЛЯ WINDOWS ========================
# Добавляем FFmpeg в PATH (для PyCharm/PowerShell)
ffmpeg_path = r"C:\ffmpeg\bin"
if ffmpeg_path not in os.environ["PATH"]:
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]
    print(f"✅ Добавлен ffmpeg в PATH: {ffmpeg_path}")

# Указываем pydub явные пути к FFmpeg
AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
AudioSegment.ffmpeg = r"C:\ffmpeg\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\ffmpeg\bin\ffprobe.exe"


# ========================================================================

class AudioProcessor:
    """Обработчик аудиофайлов для SpeechKit"""

    def __init__(self):
        self.target_sample_rate = 16000  # Hz (оптимально для SpeechKit)
        self.target_channels = 1  # моно

    def process_file(self, input_path: Path) -> Tuple[bool, str, Optional[Path]]:
        """
        Обрабатывает аудиофайл для SpeechKit

        Возвращает: (успех, сообщение, путь_к_обработанному_файлу)
        """
        try:
            print(f"\n{'=' * 60}")
            print(f"🔧 ОБРАБОТКА: {input_path.name}")
            print(f"{'=' * 60}")

            # 1. ЗАГРУЗКА ФАЙЛА
            print("📥 Загрузка файла...")
            audio = AudioSegment.from_file(str(input_path))

            print(f"📊 ИСХОДНЫЕ ПАРАМЕТРЫ:")
            print(f"   • Длительность: {len(audio) / 1000:.2f} сек")
            print(f"   • Каналы: {audio.channels} ({'моно' if audio.channels == 1 else 'стерео'})")
            print(f"   • Частота: {audio.frame_rate} Hz")
            print(f"   • Громкость: {audio.dBFS:.1f} dBFS")

            # 2. КОНВЕРТАЦИЯ В МОНО
            if audio.channels != self.target_channels:
                audio = audio.set_channels(self.target_channels)
                print(f"✅ Конвертирован в моно")

            # 3. УСТАНОВКА ЧАСТОТЫ ДИСКРЕТИЗАЦИИ
            if audio.frame_rate != self.target_sample_rate:
                audio = audio.set_frame_rate(self.target_sample_rate)
                print(f"✅ Частота установлена: {self.target_sample_rate} Hz")

            # 4. НОРМАЛИЗАЦИЯ ГРОМКОСТИ
            audio = normalize(audio)
            print(f"✅ Громкость нормализована: {audio.dBFS:.1f} dBFS")

            # 5. КОМПРЕССИЯ ДИНАМИЧЕСКОГО ДИАПАЗОНА
            audio = compress_dynamic_range(audio)
            print(f"✅ Динамический диапазон сжат")

            # 6. ОБРЕЗКА ТИШИНЫ
            audio = self._trim_silence(audio)

            # 7. ПРОВЕРКА РЕЗУЛЬТАТА
            print(f"\n📊 РЕЗУЛЬТАТ:")
            print(f"   • Длительность: {len(audio) / 1000:.2f} сек")
            print(f"   • Каналы: {audio.channels}")
            print(f"   • Частота: {audio.frame_rate} Hz")
            print(f"   • Громкость: {audio.dBFS:.1f} dBFS")

            # 8. СОХРАНЕНИЕ В ФОРМАТЕ ДЛЯ SPEECHKIT
            output_path = self._get_output_path(input_path)

            audio.export(
                str(output_path),
                format="wav",
                parameters=[
                    "-ac", str(self.target_channels),  # моно
                    "-ar", str(self.target_sample_rate),  # 16000 Hz
                    "-acodec", "pcm_s16le"  # 16-bit PCM
                ]
            )

            file_size_kb = output_path.stat().st_size / 1024
            print(f"💾 Сохранен: {output_path.name} ({file_size_kb:.1f} KB)")

            return True, "Файл успешно обработан", output_path

        except Exception as e:
            error_msg = f"Ошибка обработки: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg, None

    def _trim_silence(self, audio: AudioSegment) -> AudioSegment:
        """Обрезает тишину в начале и конце"""
        silence_threshold = -40  # dBFS

        def detect_silence(audio_segment, chunk=10):
            trim_ms = 0
            while trim_ms < len(audio_segment):
                if audio_segment[trim_ms:trim_ms + chunk].dBFS < silence_threshold:
                    trim_ms += chunk
                else:
                    break
            return trim_ms

        # Обрезаем в начале
        start_trim = detect_silence(audio)
        # Обрезаем в конце
        end_trim = detect_silence(audio.reverse())

        if start_trim > 0 or end_trim > 0:
            duration = len(audio)
            trimmed = audio[start_trim:duration - end_trim]
            print(f"✅ Обрезана тишина: {start_trim / 1000:.1f}с в начале, {end_trim / 1000:.1f}с в конце")
            return trimmed

        return audio

    def _get_output_path(self, input_path: Path) -> Path:
        """Генерирует путь для сохранения обработанного файла"""
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / f"{input_path.stem}_processed.wav"


def process_single_file(file_path: str):
    """Обрабатывает один файл"""
    processor = AudioProcessor()
    input_path = Path(file_path)

    if not input_path.exists():
        print(f"❌ Файл не найден: {file_path}")
        return

    success, message, output_path = processor.process_file(input_path)

    if success and output_path:
        print(f"\n{'=' * 60}")
        print(f"✅ УСПЕХ! Файл готов для SpeechKit")
        print(f"📁 Исходный: {input_path.name}")
        print(f"📁 Обработанный: {output_path.name}")
        print(f"{'=' * 60}")

        # Тестируем транскрибацию сразу
        test_transcription(output_path)
    else:
        print(f"\n❌ ОШИБКА: {message}")


def test_transcription(audio_path: Path):
    """Тестирует транскрибацию обработанного файла"""
    print(f"\n🎤 ТЕСТИРУЮ ТРАНСКРИБАЦИЮ...")

    try:
        import requests
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.getenv('YANDEX_API_KEY')
        folder_id = os.getenv('YANDEX_FOLDER_ID')

        if not api_key or not folder_id:
            print("❌ Не найдены ключи в .env файле")
            return

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
            "sampleRateHertz": "16000",  # Соответствует нашей обработке
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

            if text:
                print(f"🎉 УСПЕХ! Распознанный текст ({len(text)} символов):")
                print(f"{'-' * 40}")
                print(text)
                print(f"{'-' * 40}")

                # Сохраняем результат
                output_dir = Path("data/output")
                output_dir.mkdir(exist_ok=True)

                with open(output_dir / f"transcript_{audio_path.stem}.txt", 'w', encoding='utf-8') as f:
                    f.write(text)

                print(f"💾 Транскрипция сохранена: data/output/transcript_{audio_path.stem}.txt")
            else:
                print(f"⚠️  SpeechKit вернул пустой текст")
                print(f"   Возможно, в файле действительно нет речи или она неразборчива")
        else:
            print(f"❌ Ошибка SpeechKit: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")


if __name__ == "__main__":
    print("=" * 70)
    print("🎵 ПРОЦЕССОР АУДИО ДЛЯ SPEECHKIT")
    print("=" * 70)

    # Проверяем наличие тестового файла
    test_file = "data/input/1350033465.mp3"

    if Path(test_file).exists():
        print(f"📁 Тестовый файл: {test_file}")
        process_single_file(test_file)
    else:
        print(f"❌ Тестовый файл не найден: {test_file}")
        print("\n📂 Доступные файлы в data/input/:")
        input_dir = Path("data/input")
        if input_dir.exists():
            for file in input_dir.glob("*.mp3"):
                print(f"   • {file.name}")
        else:
            print(f"   Папка data/input/ не существует")

        print(f"\n💡 Использование: python audio_processor_final.py <путь_к_файлу>")
        print(f"   Пример: python audio_processor_final.py data/input/ваш_файл.mp3")