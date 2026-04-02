"""
test_safe.py - безопасная проверка перед запуском
"""
import os
from pathlib import Path
from dotenv import load_dotenv

print("=" * 60)
print("🔍 ПРОВЕРКА ПЕРЕД ЗАПУСКОМ ОБРАБОТКИ")
print("=" * 60)

# 1. Проверка .env
print("1. 📁 Проверка .env файла...")
load_dotenv()

required_vars = ['YANDEX_API_KEY', 'YANDEX_FOLDER_ID']
missing = []
for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"   ✅ {var}: есть (первые 5 символов: {value[:5]}...)")
    else:
        print(f"   ❌ {var}: ОТСУТСТВУЕТ")
        missing.append(var)

if missing:
    print(f"\n⚠️  ВНИМАНИЕ: В .env отсутствуют: {', '.join(missing)}")
    print("   Заполните .env на основе .env.example")
else:
    print(f"\n✅ .env файл в порядке")

# 2. Проверка папок
print("\n2. 📂 Проверка структуры папок...")
folders = ['data/input', 'data/processed', 'data/output']
for folder in folders:
    path = Path(folder)
    if path.exists():
        print(f"   ✅ {folder}/: существует")
    else:
        print(f"   ❌ {folder}/: не существует")

# 3. Проверка файлов
print("\n3. 🎵 Проверка аудиофайлов...")
input_dir = Path('data/input')
if input_dir.exists():
    mp3_files = list(input_dir.glob('*.mp3'))
    if mp3_files:
        print(f"   ✅ MP3 файлов найдено: {len(mp3_files)}")
        for f in mp3_files[:3]:  # покажем первые 3
            print(f"     • {f.name} ({f.stat().st_size/1024:.1f} KB)")
    else:
        print(f"   ⚠  В {input_dir} нет MP3 файлов")
else:
    print(f"   ❌ Папка {input_dir} не существует")

# 4. Проверка FFmpeg
print("\n4. 🔧 Проверка FFmpeg...")
try:
    import subprocess
    result = subprocess.run(['ffmpeg', '-version'],
                          capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        print(f"   ✅ FFmpeg работает")
        version = result.stdout.split('\n')[0].split()[2]
        print(f"     Версия: {version}")
    else:
        print(f"   ❌ FFmpeg ошибка: {result.stderr[:100]}")
except Exception as e:
    print(f"   ❌ FFmpeg не найден: {e}")

print("\n" + "=" * 60)
print("📋 ИТОГ:")
print("-" * 60)

if not missing and input_dir.exists() and len(list(input_dir.glob('*.mp3'))) > 0:
    print("✅ Всё готово для запуска обработки!")
    print("💡 Запустите: python src\\services\\audio_processor_final.py")
else:
    print("⚠️  Требуются исправления перед запуском")

print("=" * 60)