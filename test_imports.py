"""
test_imports.py - проверка установки библиотек
"""
print("=" * 50)
print("ПРОВЕРКА УСТАНОВКИ БИБЛИОТЕК")
print("=" * 50)

# 1. Проверка numpy
try:
    import numpy as np
    print(f"✅ numpy: установлен (версия: {np.__version__})")
except ImportError as e:
    print(f"❌ numpy: НЕ установлен")
    print(f"   Ошибка: {e}")

# 2. Проверка pydub
try:
    from pydub import AudioSegment
    print(f"✅ pydub: установлен")
except ImportError as e:
    print(f"❌ pydub: НЕ установлен")
    print(f"   Ошибка: {e}")

# 3. Проверка noisereduce
try:
    import noisereduce as nr
    print(f"✅ noisereduce: установлен")
except ImportError as e:
    print(f"❌ noisereduce: НЕ установлен")
    print(f"   Ошибка: {e}")

# 4. Проверка soundfile
try:
    import soundfile as sf
    print(f"✅ soundfile: установлен (версия: {sf.__version__})")
except ImportError as e:
    print(f"❌ soundfile: НЕ установлен")
    print(f"   Ошибка: {e}")

# 5. Проверка scipy (нужен для noisereduce)
try:
    import scipy
    print(f"✅ scipy: установлен (версия: {scipy.__version__})")
except ImportError as e:
    print(f"❌ scipy: НЕ установлен")
    print(f"   Ошибка: {e}")

# 6. Проверка Python пути
import sys
print(f"\n📁 Путь Python: {sys.executable}")

# 7. Проверка FFmpeg
import subprocess
try:
    result = subprocess.run(['ffmpeg', '-version'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ FFmpeg: установлен")
    else:
        print(f"❌ FFmpeg: ошибка при запуске")
except FileNotFoundError:
    print(f"❌ FFmpeg: НЕ найден в PATH")

print("=" * 50)