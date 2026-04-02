"""
check_sys.py - проверка встроенных модулей
"""
print("=" * 50)
print("ПРОВЕРКА ВСТРОЕННЫХ МОДУЛЕЙ PYTHON")
print("=" * 50)

# Проверка sys
try:
    import sys
    print(f"✅ sys: Python {sys.version}")
except ImportError:
    print("❌ sys: ОШИБКА - это невозможно!")

# Проверка os
try:
    import os
    print(f"✅ os: работает")
except ImportError:
    print("❌ os: ОШИБКА")

# Проверка pathlib
try:
    import pathlib
    print(f"✅ pathlib: работает")
except ImportError:
    print("❌ pathlib: ОШИБКА")

print("=" * 50)