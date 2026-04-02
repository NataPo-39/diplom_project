"""
async_transcriber.py - Асинхронная транскрибация длинных аудиофайлов
Использует асинхронный REST API Yandex SpeechKit + Object Storage
"""

import sys
import os
import time
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
import requests
import boto3
from botocore.config import Config

# Исправляем пути
PART2_ROOT = Path(__file__).parent.parent.parent
SRC_PATH = PART2_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Импорты
try:
    from utils.config import config
    print("✅ config импортирован")
except ImportError as e:
    print(f"❌ Ошибка импорта config: {e}")
    print(f"   Путь поиска: {SRC_PATH}")
    sys.exit(1)


class AsyncTranscriber:
    """
    Асинхронный транскрибатор для длинных аудиофайлов
    """

    def __init__(self):
        self.api_key = config.get('yandex_api_key')
        self.folder_id = config.get('yandex_folder_id')

        # S3 настройки — читаем напрямую из переменных окружения
        self.access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.bucket_name = os.getenv('BUCKET_NAME')
        self.endpoint_url = os.getenv('S3_ENDPOINT_URL', 'https://storage.yandexcloud.net')

        # URL для асинхронного API
        self.async_url = "https://transcribe.api.cloud.yandex.net/speech/stt/v2/longRunningRecognize"

        # Папка для результатов
        self.output_dir = PART2_ROOT / "data" / "transcriptions"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Инициализация S3 клиента
        self.s3_client = self._init_s3_client()

        print(f"✅ AsyncTranscriber инициализирован")
        print(f"   📁 Сохранение: {self.output_dir}")
        print(f"   🪣 Бакет: {self.bucket_name}")

    def _init_s3_client(self):
        """Инициализирует клиент S3 (Object Storage)"""
        if not all([self.access_key, self.secret_key, self.bucket_name]):
            print("⚠️ S3 ключи не настроены, загрузка в Object Storage недоступна")
            return None
        try:
            session = boto3.session.Session()
            client = session.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(signature_version='s3v4')
            )
            print("✅ S3 клиент инициализирован")
            return client
        except Exception as e:
            print(f"❌ Ошибка инициализации S3: {e}")
            return None

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }

    def upload_to_object_storage(self, audio_path: Path) -> Optional[str]:
        if not self.s3_client:
            print("   ⚠️ S3 клиент не инициализирован, пропускаем")
            return None

        object_key = f"audio/{datetime.now().strftime('%Y-%m-%d')}/{uuid.uuid4()}{audio_path.suffix}"
        try:
            print(f"   📤 Загрузка: {audio_path.name} → {object_key}")
            with open(audio_path, 'rb') as f:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_key,
                    Body=f,
                    ContentType='audio/wav'
                )
            # Формируем HTTPS URL (без завершающего слеша в endpoint_url)
            base_url = self.endpoint_url.rstrip('/')
            url = f"{base_url}/{self.bucket_name}/{object_key}"
            print(f"   ✅ URL: {url}")
            return url
        except Exception as e:
            print(f"   ❌ Ошибка загрузки: {e}")
            return None

    def start_recognition(self, audio_uri: str) -> Optional[str]:
        """
        Запускает асинхронное распознавание
        """
        payload = {
            "config": {
                "specification": {
                    "languageCode": "ru-RU",
                    "model": "general",
                    "audioEncoding": "LINEAR16_PCM",
                    "sampleRateHertz": 16000,
                    "audioChannelCount": 1
                }
            },
            "audio": {
                "uri": audio_uri
            }
        }

        try:
            response = requests.post(
                self.async_url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                operation_id = result.get("id")
                print(f"   🆔 Задача запущена: {operation_id}")
                return operation_id
            else:
                print(f"   ❌ Ошибка запуска: {response.status_code} {response.text[:200]}")
                return None
        except Exception as e:
            print(f"   ❌ Исключение: {e}")
            return None

    def get_recognition_result(self, operation_id: str, max_wait: int = 300) -> Optional[str]:
        """
        Ожидает завершения операции и возвращает текст
        """
        url = f"https://operation.api.cloud.yandex.net/operations/{operation_id}"
        wait_time = 0
        poll_interval = 5

        while wait_time < max_wait:
            try:
                response = requests.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    data = response.json()
                    if data.get("done", False):
                        if "response" in data:
                            # Извлечение текста из ответа
                            chunks = data["response"].get("chunks", [])
                            texts = []
                            for chunk in chunks:
                                for alt in chunk.get("alternatives", []):
                                    text = alt.get("text", "")
                                    if text:
                                        texts.append(text)
                            return " ".join(texts)
                        elif "error" in data:
                            print(f"   ❌ Ошибка операции: {data['error']}")
                            return None
                    else:
                        print(f"   ⏳ Ожидание... ({wait_time}/{max_wait} сек)")
                        time.sleep(poll_interval)
                        wait_time += poll_interval
                else:
                    print(f"   ❌ Ошибка проверки: {response.status_code}")
                    return None
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
                return None

        print(f"   ⏰ Таймаут {max_wait} сек")
        return None

    def transcribe_audio(self, audio_path: Path) -> Optional[Dict[str, Any]]:
        """
        Полный цикл: загрузка в S3, запуск распознавания, получение результата
        """
        print(f"\n🎙️ Транскрибация: {audio_path.name}")
        print(f"   Размер: {audio_path.stat().st_size / 1024:.1f} KB")

        # Загружаем в S3
        audio_uri = self.upload_to_object_storage(audio_path)
        if not audio_uri:
            return None

        # Запускаем распознавание
        operation_id = self.start_recognition(audio_uri)
        if not operation_id:
            return None

        # Получаем результат
        text = self.get_recognition_result(operation_id)
        if not text:
            return None

        # Сохраняем результат
        result = {
            "filename": audio_path.name,
            "timestamp": datetime.now().isoformat(),
            "operation_id": operation_id,
            "text": text,
            "text_length": len(text),
            "audio_size_kb": audio_path.stat().st_size / 1024
        }

        output_file = self.output_dir / f"{audio_path.stem}_transcript.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"   💾 Сохранен: {output_file.name}")
        print(f"   📝 Текст: {text[:100]}...")
        return result

    def transcribe_all(self, audio_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Транскрибирует все WAV-файлы в указанной папке
        """
        if audio_dir is None:
            audio_dir = PART2_ROOT / "data" / "generated" / "audio"

        audio_files = list(audio_dir.glob("*.wav"))
        if not audio_files:
            print(f"⚠️ В папке {audio_dir} нет WAV-файлов")
            return []

        print(f"📁 Найдено WAV-файлов: {len(audio_files)}")
        results = []

        for i, f in enumerate(audio_files, 1):
            print(f"\n🔹 {i}/{len(audio_files)}")
            result = self.transcribe_audio(f)
            if result:
                results.append(result)
            time.sleep(2)  # небольшая пауза между файлами

        print(f"\n✅ Транскрибировано: {len(results)}")
        return results


if __name__ == "__main__":
    print("🧪 Тестирование AsyncTranscriber")
    print("=" * 60)

    # Добавим отладочный вывод переменных окружения
    print("Проверка переменных окружения:")
    for var in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'BUCKET_NAME', 'S3_ENDPOINT_URL']:
        val = os.getenv(var)
        if val:
            print(f"   {var}: {val[:10]}...")
        else:
            print(f"   {var}: не задана")

    transcriber = AsyncTranscriber()
    results = transcriber.transcribe_all()

    if results:
        print("\n📊 Результаты:")
        for r in results:
            print(f"   - {r['filename']}: {r['text_length']} символов")
    else:
        print("⚠️ Ничего не транскрибировано")

    print("\n" + "=" * 60)