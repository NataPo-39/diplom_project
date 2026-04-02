import os
import boto3
from pathlib import Path
from dotenv import load_dotenv


def upload_audio_files(local_folder: str = "data/input", bucket_prefix: str = "incoming/"):
    """
    Загружает все аудиофайлы из локальной папки в бакет Object Storage.
    """
    # Загружаем переменные из .env
    load_dotenv()

    # Получаем ключи из .env
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    bucket_name = os.getenv("BUCKET_NAME", "call-audio-ponart")

    if not access_key or not secret_key:
        print("❌ Ошибка: Не найдены ключи доступа в .env файле")
        print("   Добавь в .env:")
        print("   AWS_ACCESS_KEY_ID=your_key")
        print("   AWS_SECRET_ACCESS_KEY=your_secret")
        return None  # Возвращаем None вместо просто return

    # Создаём клиент для Yandex Object Storage
    s3_client = boto3.client(
        's3',
        endpoint_url='https://storage.yandexcloud.net',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

    # Проверяем существование локальной папки
    local_path = Path(local_folder)
    if not local_path.exists():
        print(f"❌ Локальная папка не найдена: {local_folder}")
        print(f"   Создай папку и положи туда аудиофайлы")
        return s3_client, bucket_name  # Возвращаем клиента для использования позже

    # Получаем список аудиофайлов
    audio_files = list(local_path.glob("*.mp3")) + list(local_path.glob("*.wav"))

    if not audio_files:
        print(f"❌ В папке {local_folder} нет MP3/WAV файлов")
        return s3_client, bucket_name

    print(f"📁 Найдено {len(audio_files)} аудиофайлов в {local_folder}")
    print(f"☁️  Загружаю в бакет: {bucket_name}/{bucket_prefix}")

    # Загружаем каждый файл
    uploaded_count = 0
    for audio_file in audio_files:
        # Имя файла в бакете (с префиксом папки)
        object_key = f"{bucket_prefix}{audio_file.name}"

        try:
            s3_client.upload_file(
                str(audio_file),  # Локальный путь
                bucket_name,  # Имя бакета
                object_key  # Путь в бакете
            )
            print(f"✅ Загружен: {audio_file.name} → {object_key}")
            uploaded_count += 1
        except Exception as e:
            print(f"❌ Ошибка при загрузке {audio_file.name}: {e}")

    print(f"\n🎯 Итого: {uploaded_count}/{len(audio_files)} файлов загружено")
    print(f"📊 Бакет: {bucket_name}")
    print(f"📁 Папка в бакете: {bucket_prefix}")

    return s3_client, bucket_name  # Возвращаем для использования в main


def create_folders(s3_client, bucket_name):
    """Создаёт пустые папки в бакете"""
    for folder in ["processed/", "errors/"]:
        try:
            # Создаём пустой объект (это создаст "папку" в интерфейсе)
            s3_client.put_object(Bucket=bucket_name, Key=folder)
            print(f"📁 Создана папка: {folder}")
        except Exception as e:
            print(f"⚠️  Не удалось создать папку {folder}: {e}")


if __name__ == "__main__":
    # Загружаем файлы и получаем клиент
    result = upload_audio_files("data/input", "incoming/")

    if result:
        s3_client, bucket_name = result
        # Создаём дополнительные папки
        create_folders(s3_client, bucket_name)