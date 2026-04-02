"""
test_audio_content.py - проверка содержимого аудиофайла
"""
import os
from pathlib import Path
from pydub import AudioSegment
import numpy as np

# Настройка FFmpeg
os.environ["PATH"] = r"C:\ffmpeg\bin;" + os.environ["PATH"]
AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"


def analyze_audio_content(file_path: Path):
    """Анализирует, есть ли речь в аудиофайле"""
    print("=" * 70)
    print(f"🔍 АНАЛИЗ АУДИОФАЙЛА: {file_path.name}")
    print("=" * 70)

    try:
        # Загружаем аудио
        audio = AudioSegment.from_file(str(file_path))

        print(f"📊 Основные параметры:")
        print(f"   • Длительность: {len(audio) / 1000:.2f} сек")
        print(f"   • Каналы: {audio.channels} ({'моно' if audio.channels == 1 else 'стерео'})")
        print(f"   • Частота: {audio.frame_rate} Hz")
        print(f"   • Громкость: {audio.dBFS:.1f} dBFS")

        # Получаем сырые данные
        samples = np.array(audio.get_array_of_samples())

        if len(samples) == 0:
            print(f"❌ Файл не содержит аудиоданных")
            return

        print(f"\n📈 Анализ аудиосигнала:")

        # 1. Максимальная амплитуда
        max_amplitude = np.max(np.abs(samples))
        max_possible = audio.max_possible_amplitude
        amplitude_percent = (max_amplitude / max_possible) * 100
        print(f"   • Макс. амплитуда: {max_amplitude:,} / {max_possible:,} ({amplitude_percent:.1f}%)")

        # 2. Средняя энергия
        energy = np.mean(samples.astype(float) ** 2)
        print(f"   • Энергия сигнала: {energy:.2f}")

        # 3. Процент "тишины" (амплитуда < 1% от максимума)
        silence_threshold = max_amplitude * 0.01
        silent_samples = np.sum(np.abs(samples) < silence_threshold)
        silence_percent = (silent_samples / len(samples)) * 100
        print(f"   • Тишина: {silence_percent:.1f}% амплитуды < {silence_threshold:,.0f}")

        # 4. Статистика амплитуды
        amplitude_std = np.std(samples)
        print(f"   • Стандартное отклонение: {amplitude_std:.1f}")

        # 5. Частотный анализ (грубый)
        if len(samples) > 1000:
            fft_result = np.fft.rfft(samples[:1000])
            freq_magnitudes = np.abs(fft_result)
            dominant_freq = np.argmax(freq_magnitudes) * audio.frame_rate / 1000
            print(f"   • Доминирующая частота: {dominant_freq:.0f} Hz")

        # 6. Определяем тип сигнала
        print(f"\n🔬 ОПРЕДЕЛЕНИЕ ТИПА СИГНАЛА:")

        if amplitude_percent < 0.1:
            print(f"   ❌ ОЧЕНЬ ТИХИЙ: амплитуда всего {amplitude_percent:.1f}% от максимума")
            print(f"   → SpeechKit не услышит такой тихий звук")
        elif silence_percent > 95:
            print(f"   ❌ ПРАКТИЧЕСКАЯ ТИШИНА: {silence_percent:.1f}% сигнала - тишина")
            print(f"   → Файл почти беззвучный")
        elif amplitude_std < 100:
            print(f"   ⚠️  МОНОТОННЫЙ СИГНАЛ: мало вариаций (std={amplitude_std:.1f})")
            print(f"   → Возможно, это не речь, а тон/сигнал")
        else:
            print(f"   ✅ СИГНАЛ ЕСТЬ: амплитуда {amplitude_percent:.1f}%, вариаций достаточно")
            print(f"   → Проблема в параметрах SpeechKit")

        # 7. Сохраняем фрагмент для прослушивания
        save_sample_for_listening(audio, file_path)

    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")


def save_sample_for_listening(audio: AudioSegment, original_path: Path):
    """Сохраняет фрагмент файла для прослушивания"""
    try:
        # Берём первые 5 секунд или весь файл если он короче
        sample_duration = min(5000, len(audio))  # 5 секунд в миллисекундах
        sample = audio[:sample_duration]

        output_dir = Path("data/samples")
        output_dir.mkdir(exist_ok=True)

        sample_path = output_dir / f"sample_{original_path.stem}.wav"
        sample.export(str(sample_path), format="wav")

        print(f"\n💾 Образец для прослушивания:")
        print(f"   📁 {sample_path}")
        print(f"   ⏱️  {sample_duration / 1000:.1f} секунд")
        print(f"   🔊 Скопируйте и откройте в аудиоплеере")

    except Exception as e:
        print(f"   ⚠️  Не удалось сохранить образец: {e}")


def listen_to_sample():
    """Пытается воспроизвести образец (если возможно)"""
    import platform
    system = platform.system()

    print(f"\n🎧 ВОСПРОИЗВЕДЕНИЕ ОБРАЗЦА:")

    samples_dir = Path("data/samples")
    if samples_dir.exists():
        sample_files = list(samples_dir.glob("*.wav"))
        if sample_files:
            sample_file = sample_files[0]
            print(f"   Файл: {sample_file.name}")

            if system == "Windows":
                print(f"   💡 На Windows: откройте файл в медиаплеере")
                print(f"   📍 Путь: {sample_file.absolute()}")
            elif system == "Darwin":  # macOS
                print(f"   💡 На macOS: открыть через QuickTime")
            else:  # Linux
                print(f"   💡 На Linux: use aplay или mpg123")

    print(f"   🎵 ИЛИ просто откройте файл дважды кликом")


if __name__ == "__main__":
    # Анализируем самый короткий файл
    test_file = Path("data/input/1350033465.mp3")

    if test_file.exists():
        analyze_audio_content(test_file)
        listen_to_sample()
    else:
        print(f"❌ Файл не найден: {test_file}")

    input("\nНажмите Enter для выхода...")