
"""
fix_ffmpeg.py - исправление пути к ffmpeg для всех случаев
"""
import os
import subprocess
import sys


def fix_ffmpeg_path():
    """Добавляет ffmpeg в PATH и проверяет работу"""

    ffmpeg_bin = r"C:\ffmpeg\bin"

    # Добавляем в PATH
    if ffmpeg_bin not in os.environ["PATH"]:
        os.environ["PATH"] = ffmpeg_bin + os.pathsep + os.environ["PATH"]
        print(f"✅ Добавлен в PATH: {ffmpeg_bin}")

    # Проверяем ffmpeg
    try:
        # Для Windows используем shell=True
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            shell=True,  # Важно для Windows!
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode == 0:
            print("✅ FFmpeg работает!")
            # Выводим первую строку с версией
            lines = result.stdout.strip().split('\n')
            if lines:
                print(f"📊 {lines[0]}")
            return True
        else:
            print(f"❌ FFmpeg ошибка (код {result.returncode})")
            print(f"Ошибка: {result.stderr[:200]}")
            return False

    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("ИСПРАВЛЕНИЕ ПУТИ К FFMPEG")
    print("=" * 50)

    success = fix_ffmpeg_path()

    if success:
        print("\n✅ Готово! Теперь можно запускать audio_processor.py")
    else:
        print("\n❌ Проблема с FFmpeg. Проверьте установку.")

    input("\nНажмите Enter для выхода...")