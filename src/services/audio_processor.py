"""
Модуль для предобработки аудиофайлов перед отправкой в SpeechKit
"""
import os
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import noisereduce as nr
import soundfile as sf
import os
import sys

# ============================================
# ИСПРАВЛЕНИЕ ПУТИ К FFMPEG ДЛЯ WINDOWS
# ============================================

# Добавляем путь к ffmpeg в PATH (для PyCharm/PowerShell)
ffmpeg_path = r"C:\ffmpeg\bin"
if ffmpeg_path not in os.environ["PATH"]:
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]
    print(f"✅ Добавлен ffmpeg в PATH: {ffmpeg_path}")

# Указываем pydub явные пути к ffmpeg
try:
    from pydub import AudioSegment
    AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
    AudioSegment.ffmpeg = r"C:\ffmpeg\bin\ffmpeg.exe"
    AudioSegment.ffprobe = r"C:\ffmpeg\bin\ffprobe.exe"
    print("✅ Пути к ffmpeg установлены для pydub")
except ImportError:
    print("⚠️  pydub не установлен")

# ============================================
# ОСНОВНОЙ КОД
# ============================================
# Остальной код audio_processor.py...


class AudioProcessor:
    """Обработчик аудиофайлов для улучшения качества"""

    # Оптимальные параметры для SpeechKit
    TARGET_SAMPLE_RATE = 16000  # Hz
    TARGET_CHANNELS = 1  # моно
    TARGET_FORMAT = "wav"  # формат
    TARGET_BIT_DEPTH = 16  # бит

    def __init__(self,
                 target_sample_rate: int = 16000,
                 target_channels: int = 1):
        """
        Инициализация процессора аудио

        Args:
            target_sample_rate: Целевая частота дискретизации (Гц)
            target_channels: Количество каналов (1 = моно)
        """
        self.target_sample_rate = target_sample_rate
        self.target_channels = target_channels

    def process_file(self,
                     input_path: Path,
                     output_path: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Обрабатывает аудиофайл для SpeechKit

        Args:
            input_path: Путь к исходному файлу
            output_path: Путь для сохранения (если None, создается автоматически)

        Returns:
            Tuple[успех, сообщение]
        """
        try:
            print(f"🔧 Обработка: {input_path.name}")

            # 1. Загружаем аудио
            audio = self._load_audio(input_path)

            # 2. Анализируем исходное качество
            self._analyze_audio(audio, "Исходное")

            # 3. Применяем обработку
            processed_audio = self._apply_processing_pipeline(audio)

            # 4. Анализируем результат
            self._analyze_audio(processed_audio, "Обработанное")

            # 5. Определяем путь для сохранения
            if output_path is None:
                output_path = self._get_output_path(input_path)

            # 6. Сохраняем в оптимальном формате для SpeechKit
            self._save_audio(processed_audio, output_path)

            return True, f"Файл обработан: {output_path}"

        except Exception as e:
            return False, f"Ошибка обработки: {e}"

    def _load_audio(self, file_path: Path) -> AudioSegment:
        """Загружает аудиофайл"""
        return AudioSegment.from_file(str(file_path))

    def _analyze_audio(self, audio: AudioSegment, label: str):
        """Анализирует параметры аудио"""
        print(f"   📊 {label} аудио:")
        print(f"     - Длительность: {len(audio) / 1000:.2f} сек")
        print(f"     - Каналы: {audio.channels}")
        print(f"     - Частота: {audio.frame_rate} Hz")
        print(f"     - Громкость: {audio.dBFS:.1f} dBFS")

        # Проверка на тишину
        if audio.dBFS < -50:
            print(f"     ⚠  Очень тихо! ({audio.dBFS:.1f} dBFS)")

    def _apply_processing_pipeline(self, audio: AudioSegment) -> AudioSegment:
        """
        Применяет пайплайн обработки аудио
        """
        processed = audio

        # 1. Конвертация в моно
        if processed.channels != self.target_channels:
            processed = processed.set_channels(self.target_channels)
            print("   ✅ Конвертирован в моно")

        # 2. Установка частоты дискретизации
        if processed.frame_rate != self.target_sample_rate:
            processed = processed.set_frame_rate(self.target_sample_rate)
            print(f"   ✅ Частота установлена: {self.target_sample_rate} Hz")

        # 3. Удаление шума (если установлена библиотека noisereduce)
        try:
            processed = self._reduce_noise(processed)
            print("   ✅ Шумоподавление применено")
        except Exception:
            print("   ⚠  Шумоподавление пропущено (требуется noisereduce)")

        # 4. Нормализация громкости
        processed = normalize(processed)
        print(f"   ✅ Громкость нормализована: {processed.dBFS:.1f} dBFS")

        # 5. Компрессия динамического диапазона
        processed = compress_dynamic_range(processed)
        print("   ✅ Динамический диапазон сжат")

        # 6. Обрезка тишины в начале/конце
        processed = self._trim_silence(processed)

        return processed

    def _reduce_noise(self, audio: AudioSegment) -> AudioSegment:
        """Применяет шумоподавление"""
        # Конвертируем в numpy array
        samples = np.array(audio.get_array_of_samples())

        # Применяем шумоподавление
        reduced_noise = nr.reduce_noise(
            y=samples.astype(np.float32),
            sr=audio.frame_rate,
            prop_decrease=0.8  # Уменьшение шума на 80%
        )

        # Конвертируем обратно в AudioSegment
        return AudioSegment(
            reduced_noise.astype(np.int16).tobytes(),
            frame_rate=audio.frame_rate,
            sample_width=audio.sample_width,
            channels=audio.channels
        )

    def _trim_silence(self, audio: AudioSegment) -> AudioSegment:
        """Обрезает тишину в начале и конце"""
        silence_threshold = -40  # dBFS
        min_silence_len = 500  # мс

        # Функция для обнаружения тишины
        def detect_silence(audio_segment, threshold, chunk=10):
            trim_ms = 0
            while trim_ms < len(audio_segment):
                if audio_segment[trim_ms:trim_ms + chunk].dBFS < threshold:
                    trim_ms += chunk
                else:
                    break
            return trim_ms

        # Обрезаем в начале
        start_trim = detect_silence(audio, silence_threshold)

        # Обрезаем в конце
        end_trim = detect_silence(audio.reverse(), silence_threshold)

        if start_trim > 0 or end_trim > 0:
            duration = len(audio)
            trimmed = audio[start_trim:duration - end_trim]
            print(f"   ✅ Обрезана тишина: {start_trim / 1000:.1f}с в начале, {end_trim / 1000:.1f}с в конце")
            return trimmed

        return audio

    def _get_output_path(self, input_path: Path) -> Path:
        """Генерирует путь для сохранения обработанного файла"""
        output_dir = Path("data/processed")
        output_dir.mkdir(exist_ok=True)

        # Меняем расширение на .wav
        return output_dir / f"{input_path.stem}_processed.wav"

    def _save_audio(self, audio: AudioSegment, output_path: Path):
        """Сохраняет аудио в оптимальном формате для SpeechKit"""
        # Сохраняем как WAV с параметрами для SpeechKit
        audio.export(
            str(output_path),
            format="wav",
            parameters=[
                "-ac", str(self.target_channels),  # каналы
                "-ar", str(self.target_sample_rate),  # частота
                "-acodec", "pcm_s16le"  # 16-bit PCM
            ]
        )
        print(f"   💾 Сохранен: {output_path.name}")
        print(f"   📁 Размер: {output_path.stat().st_size / 1024:.1f} KB")


# Функция для быстрого использования
def process_audio_file(input_file: str, output_file: Optional[str] = None) -> bool:
    """
    Быстрая обработка одного файла

    Args:
        input_file: Путь к входному файлу
        output_file: Путь для сохранения (опционально)

    Returns:
        bool: Успех операции
    """
    processor = AudioProcessor()

    input_path = Path(input_file)
    output_path = Path(output_file) if output_file else None

    success, message = processor.process_file(input_path, output_path)

    print(f"\n{'✅' if success else '❌'} {message}")
    return success


if __name__ == "__main__":
    # Пример использования
    import sys

    if len(sys.argv) > 1:
        process_audio_file(sys.argv[1])
    else:
        print("Использование: python audio_processor.py <путь_к_файлу>")