"""
audio_processor_fixed.py - обработчик с учётом лимита 30 секунд
"""
import os
from pathlib import Path
from typing import Optional, Tuple, List
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range

# ======================== ИСПРАВЛЕНИЕ ДЛЯ WINDOWS ========================
ffmpeg_path = r"C:\ffmpeg\bin"
if ffmpeg_path not in os.environ["PATH"]:
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]

AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
AudioSegment.ffmpeg = r"C:\ffmpeg\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\ffmpeg\bin\ffprobe.exe"


# ========================================================================

class AudioProcessorFixed:
    """Обработчик аудио с учётом лимита SpeechKit (30 секунд)"""

    MAX_DURATION_MS = 30000  # 30 секунд в миллисекундах

    def __init__(self):
        self.target_sample_rate = 16000
        self.target_channels = 1

    def process_file(self, input_path: Path) -> Tuple[bool, str, List[Path]]:
        """
        Обрабатывает аудиофайл с проверкой длительности

        Возвращает: (успех, сообщение, список_путей_к_обработанным_файлам)
        """
        try:
            print(f"\n{'=' * 60}")
            print(f"🔧 ОБРАБОТКА: {input_path.name}")
            print(f"{'=' * 60}")

            # 1. Загрузка файла
            print("📥 Загрузка файла...")
            audio = AudioSegment.from_file(str(input_path))

            duration_sec = len(audio) / 1000
            print(f"📊 Длительность: {duration_sec:.2f} секунд")

            # 2. Проверка длительности
            if duration_sec > 30:
                print(f"⚠️  ВНИМАНИЕ: Файл длиннее 30 секунд ({duration_sec:.2f} сек)")
                print(f"   Разделяю на части по 30 секунд...")

                # Разделяем файл
                segments = self._split_audio(audio)
                print(f"   📁 Разделено на {len(segments)} частей")

            else:
                segments = [audio]

            # 3. Обработка каждой части
            processed_files = []

            for i, segment in enumerate(segments, 1):
                print(f"\n   Часть {i}/{len(segments)}:")

                # Обработка сегмента
                processed_segment = self._process_segment(segment)

                # Сохранение
                suffix = f"_part{i}" if len(segments) > 1 else ""
                output_path = self._get_output_path(input_path, suffix)

                self._save_audio(processed_segment, output_path)
                processed_files.append(output_path)

            return True, f"Файл обработан ({len(processed_files)} частей)", processed_files

        except Exception as e:
            return False, f"Ошибка обработки: {e}", []

    def _split_audio(self, audio: AudioSegment) -> List[AudioSegment]:
        """Разделяет аудио на части по 30 секунд"""
        segments = []

        for start_ms in range(0, len(audio), self.MAX_DURATION_MS):
            end_ms = min(start_ms + self.MAX_DURATION_MS, len(audio))
            segment = audio[start_ms:end_ms]

            if len(segment) > 1000:  # Минимум 1 секунда
                segments.append(segment)

        return segments

    def _process_segment(self, audio: AudioSegment) -> AudioSegment:
        """Обрабатывает один сегмент аудио"""
        processed = audio

        # Конвертация в моно
        if processed.channels != self.target_channels:
            processed = processed.set_channels(self.target_channels)

        # Установка частоты
        if processed.frame_rate != self.target_sample_rate:
            processed = processed.set_frame_rate(self.target_sample_rate)

        # Нормализация
        processed = normalize(processed)

        # Компрессия
        processed = compress_dynamic_range(processed)

        # Обрезка тишины
        processed = self._trim_silence(processed)

        return processed

    def _trim_silence(self, audio: AudioSegment) -> AudioSegment:
        """Обрезает тишину"""
        silence_threshold = -40

        def detect_silence(audio_segment, chunk=10):
            trim_ms = 0
            while trim_ms < len(audio_segment):
                if audio_segment[trim_ms:trim_ms + chunk].dBFS < silence_threshold:
                    trim_ms += chunk
                else:
                    break
            return trim_ms

        start_trim = detect_silence(audio)
        end_trim = detect_silence(audio.reverse())

        if start_trim > 0 or end_trim > 0:
            duration = len(audio)
            return audio[start_trim:duration - end_trim]

        return audio

    def _get_output_path(self, input_path: Path, suffix: str = "") -> Path:
        """Генерирует путь для сохранения"""
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)

        return output_dir / f"{input_path.stem}{suffix}_processed.wav"

    def _save_audio(self, audio: AudioSegment, output_path: Path):
        """Сохраняет аудио"""
        audio.export(
            str(output_path),
            format="wav",
            parameters=[
                "-ac", str(self.target_channels),
                "-ar", str(self.target_sample_rate),
                "-acodec", "pcm_s16le"
            ]
        )

        file_size_kb = output_path.stat().st_size / 1024
        print(f"   💾 Сохранен: {output_path.name} ({file_size_kb:.1f} KB)")


def test_fixed_processor():
    """Тестирует исправленный процессор"""
    processor = AudioProcessorFixed()

    # Тестовый файл (первый из списка)
    test_file = Path("data/input/1349242758.mp3")

    if test_file.exists():
        print("=" * 70)
        print("🧪 ТЕСТИРУЮ ИСПРАВЛЕННЫЙ ПРОЦЕССОР")
        print("=" * 70)

        success, message, processed_files = processor.process_file(test_file)

        if success:
            print(f"\n✅ {message}")

            # Тестируем транскрибацию каждой части
            for i, file_path in enumerate(processed_files, 1):
                print(f"\n🎤 Тестирую часть {i}...")
                test_transcription(file_path)
        else:
            print(f"\n❌ {message}")
    else:
        print(f"❌ Файл не найден: {test_file}")


def test_transcription(audio_path: Path):
    """Тестирует транскрибацию"""
    try:
        import requests
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.getenv('YANDEX_API_KEY')
        folder_id = os.getenv('YANDEX_FOLDER_ID')

        with open(audio_path, 'rb') as f:
            audio_data = f.read()

        url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        headers = {"Authorization": f"Api-Key {api_key}"}

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

        print(f"   📡 Статус: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            text = result.get("result", "")

            if text:
                print(f"   🎉 УСПЕХ! Текст ({len(text)} символов):")
                print(f"   '{text[:50]}...'" if len(text) > 50 else f"   '{text}'")
            else:
                print(f"   ⚠️  Пустой текст (возможно, нет речи)")
        else:
            print(f"   ❌ Ошибка: {response.text[:100]}")

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")


if __name__ == "__main__":
    test_fixed_processor()