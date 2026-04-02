import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Проверка переменных окружения:")
print("=" * 40)

# Проверяем ВСЕ возможные варианты
variables = {
    'Object Storage': ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'BUCKET_NAME'],
    'SpeechKit': ['YANDEX_API_KEY', 'YANDEX_FOLDER_ID', 'SPEECHKIT_API_KEY', 'YC_FOLDER_ID'],
    'Google Sheets': ['GOOGLE_SHEETS_CREDENTIALS', 'GOOGLE_SHEETS_SPREADSHEET_ID'],
    'Пути': ['INPUT_AUDIO_PATH', 'OUTPUT_CSV_PATH', 'LOG_PATH']
}

for category, vars_list in variables.items():
    print(f"\n{category}:")
    for var in vars_list:
        value = os.getenv(var)
        if value:
            # Показываем только первые 10 символов для безопасности
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"  ✅ {var}: {masked}")
        else:
            print(f"  ❌ {var}: не найден")