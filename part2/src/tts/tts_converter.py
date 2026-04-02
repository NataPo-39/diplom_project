"""
tts_converter.py - Преобразование текстовых диалогов в аудио через Yandex SpeechKit TTS
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from pydub import AudioSegment
import io

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


class TTSConverter:
    """
    Преобразователь текстовых диалогов в аудиофайлы с разными голосами
    """

    # Доступные голоса Yandex SpeechKit
    VOICES = {
        "operator": "alena",  # женский голос для оператора
        "client": "filipp"  # мужской голос для клиента
    }

    def __init__(self, input_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        """
        Инициализация TTS-конвертера
        """
        self.api_key = config.get('yandex_api_key')
        self.folder_id = config.get('yandex_folder_id')

        # URL для синтеза речи
        self.tts_url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

        # Папки
        if input_dir is None:
            self.input_dir = PART2_ROOT / "data" / "generated" / "dialogs"
        else:
            self.input_dir = Path(input_dir)

        if output_dir is None:
            self.output_dir = PART2_ROOT / "data" / "generated" / "audio"
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Пауза между репликами (в миллисекундах)
        self.pause_between_turns = 800

        print(f"✅ TTSConverter инициализирован")
        print(f"   📁 Входные JSON: {self.input_dir}")
        print(f"   📁 Выходные аудио: {self.output_dir}")

    def _synthesize(self, text: str, voice: str) -> Optional[AudioSegment]:
        """
        Синтезирует речь из текста, возвращает AudioSegment
        """
        if not text.strip():
            return None

        headers = {
            "Authorization": f"Api-Key {self.api_key}"
        }

        # Используем формат lpcm (сырой PCM)
        params = {
            "text": text,
            "lang": "ru-RU",
            "voice": voice,
            "format": "lpcm",
            "sampleRateHertz": 16000
        }

        try:
            response = requests.post(
                self.tts_url,
                headers=headers,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                # Преобразуем сырые PCM данные в AudioSegment
                # 16-bit, 16000 Hz, моно
                audio = AudioSegment.from_file(
                    io.BytesIO(response.content),
                    format="raw",
                    frame_rate=16000,
                    sample_width=2,  # 16 bit = 2 bytes
                    channels=1
                )
                return audio
            else:
                print(f"   ❌ Ошибка TTS: {response.status_code} - {response.text[:100]}")
                return None

        except Exception as e:
            print(f"   ❌ Исключение при синтезе: {e}")
            return None

    def convert_dialog(self, dialog_path: Path) -> Optional[Path]:
        """
        Преобразует один JSON-диалог в аудиофайл
        """
        print(f"\n🎙️ Обработка: {dialog_path.name}")

        # Читаем JSON
        try:
            with open(dialog_path, 'r', encoding='utf-8') as f:
                dialog_data = json.load(f)
        except Exception as e:
            print(f"   ❌ Ошибка чтения JSON: {e}")
            return None

        turns = dialog_data.get("dialog", [])
        if not turns:
            print(f"   ⚠️ Диалог не содержит реплик")
            return None

        print(f"   📝 Всего реплик: {len(turns)}")

        combined_audio = AudioSegment.silent(duration=0)

        for i, turn in enumerate(turns):
            role = turn.get("role")
            text = turn.get("text", "")

            if not text:
                continue

            if role == "user":
                voice = self.VOICES["client"]
                speaker = "Клиент"
            elif role == "assistant":
                voice = self.VOICES["operator"]
                speaker = "Оператор"
            else:
                continue

            print(f"   🔊 {speaker}: {text[:50]}...")

            audio_segment = self._synthesize(text, voice)
            if audio_segment is None:
                print(f"      ⚠️ Не удалось синтезировать реплику {i + 1}")
                continue

            combined_audio += audio_segment

            if i < len(turns) - 1:
                combined_audio += AudioSegment.silent(duration=self.pause_between_turns)

        if len(combined_audio) == 0:
            print(f"   ❌ Не удалось создать аудио")
            return None

        output_filename = dialog_path.stem + ".wav"
        output_path = self.output_dir / output_filename
        combined_audio.export(output_path, format="wav")

        print(f"   💾 Сохранен: {output_filename} (длительность: {len(combined_audio) / 1000:.1f} сек)")
        return output_path

    def convert_all(self) -> List[Path]:
        """
        Преобразует все JSON-диалоги
        """
        json_files = list(self.input_dir.glob("*.json"))
        if not json_files:
            print(f"⚠️ В папке {self.input_dir} нет JSON-файлов")
            return []

        print(f"📁 Найдено JSON-файлов: {len(json_files)}")
        results = []

        for i, json_file in enumerate(json_files, 1):
            print(f"\n🔹 {i}/{len(json_files)}")
            audio_path = self.convert_dialog(json_file)
            if audio_path:
                results.append(audio_path)
            time.sleep(0.5)

        print(f"\n✅ Преобразовано диалогов: {len(results)}")
        return results


if __name__ == "__main__":
    print("🧪 Тестирование TTSConverter")
    print("=" * 60)

    converter = TTSConverter()
    audio_files = converter.convert_all()

    if audio_files:
        print(f"\n🎵 Создано аудиофайлов:")
        for f in audio_files:
            print(f"   - {f.name}")
    else:
        print("⚠️ Ничего не создано")

    print("\n" + "=" * 60)