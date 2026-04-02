"""
test_pydub_ffmpeg.py - проверка работы pydub с ffmpeg
"""
import os
import sys

# Добавляем ffmpeg в PATH
os.environ["PATH"] = r"C:\ffmpeg\bin;" + os.environ["PATH"]

print("=" * 60)
print("ТЕСТ PYDUB С FFMPEG")
print("=" * 60)

try:
    # Указываем явные пути для pydub
    from pydub import AudioSegment

    AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
    AudioSegment.ffmpeg = r"C:\ffmpeg\bin\ffmpeg.exe"
    AudioSegment.ffprobe = r"C:\ffmpeg\bin\ffprobe.exe"

    print("✅ pydub импортирован")

    # Проверяем чтение файла
    test_file = "data/input/1350033465.mp3"
    if os.path.exists(test_file):
        print(f"📁 Тестовый файл: {test_file}")

        # Загружаем аудио
        audio = AudioSegment.from_file(test_file)

        print("✅ Файл успешно загружен!")
        print(f"📊 Параметры аудио:")
        print(f"   • Длительность: {len(audio) / 1000:.2f} секунд")
        print(f"   • Каналы: {audio.channels} ({'моно' if audio.channels == 1 else 'стерео'})")
        print(f"   • Частота дискретизации: {audio.frame_rate} Hz")
        print(f"   • Битность: {audio.sample_width * 8}-bit")
        print(f"   • Громкость: {audio.dBFS:.1f} dBFS")

        # Проверяем, есть ли звук
        if audio.dBFS < -50:
            print(f"⚠️  ВНИМАНИЕ: Очень тихая запись ({audio.dBFS:.1f} dBFS)")
        else:
            print(f"✅ Громкость в норме")

    else:
        print(f"❌ Тестовый файл не найден: {test_file}")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback

    traceback.print_exc()

print("=" * 60)