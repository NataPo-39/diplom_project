"""
dialog_generator.py - Генерация синтетических диалогов через Yandex GPT
Создает диалоги по заданным сценариям для последующего анализа
"""

import sys
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests

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


class DialogGenerator:
    """
    Генератор синтетических диалогов для обучения и анализа
    """

    def __init__(self, scenarios_path: Optional[Path] = None):
        """
        Инициализация генератора

        Args:
            scenarios_path: путь к файлу со сценариями
        """
        # Загружаем конфигурацию
        self.api_key = config.get('yandex_api_key')
        self.folder_id = config.get('yandex_folder_id')
        self.model_uri = "gpt://b1gtp8bn97gg21fl5e9j/yandexgpt-5.1/latest"
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

        # Определяем путь к сценариям
        if scenarios_path is None:
            self.scenarios_path = PART2_ROOT / "data" / "scenarios" / "dialog_scenarios.json"
        else:
            self.scenarios_path = Path(scenarios_path)

        # Загружаем сценарии
        self.scenarios = self._load_scenarios()

        # Папка для сохранения результатов
        self.output_dir = PART2_ROOT / "data" / "generated" / "dialogs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"✅ DialogGenerator инициализирован")
        print(f"   📁 Сценарии: {self.scenarios_path}")
        print(f"   📊 Загружено сценариев: {len(self.scenarios)}")
        print(f"   📁 Сохранение: {self.output_dir}")

    def _load_scenarios(self) -> List[Dict[str, Any]]:
        """Загружает сценарии из JSON-файла"""
        if not self.scenarios_path.exists():
            print(f"⚠️ Файл сценариев не найден: {self.scenarios_path}")
            return []

        try:
            with open(self.scenarios_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("scenarios", [])
        except Exception as e:
            print(f"❌ Ошибка загрузки сценариев: {e}")
            return []

    def _build_generation_prompt(self, scenario: Dict[str, Any]) -> str:
        """
        Формирует промпт для генерации диалога

        Args:
            scenario: сценарий диалога

        Returns:
            str: промпт для Yandex GPT
        """
        prompt = f"""
Сгенерируй диалог между КЛИЕНТОМ и ОПЕРАТОРОМ компании CULT CONSTRUCTIONS (премиальные алюминиевые ограждения).

СЦЕНАРИЙ: {scenario.get('name', '')}
ОПИСАНИЕ: {scenario.get('description', '')}

ОСОБЕННОСТИ:
- Клиент: {scenario.get('client_objection', '')}
- Стратегия оператора: {scenario.get('operator_strategy', '')}
- Ожидаемый результат: {scenario.get('expected_outcome', '')}

ПРИМЕРЫ ФРАЗ КЛИЕНТА (используй как ориентир, но не копируй дословно):
{chr(10).join(['- ' + p for p in scenario.get('client_phrases', [])])}

ТРЕБОВАНИЯ К ДИАЛОГУ:
1. Диалог должен состоять из 6-12 реплик (переключений между участниками)
2. Используй формат: "Клиент: [текст]" и "Оператор: [текст]"
3. Оператор должен работать по скрипту компании (премиальный сегмент, индивидуальный подход)
4. Диалог должен быть реалистичным и естественным
5. В конце диалога клиент должен оставить контакт (телефон) или согласиться на замер

ВАЖНО: 
- Оператор не называет точную стоимость (только ориентиры)
- Оператор подчеркивает преимущества: долговечность (100+ лет), отсутствие коррозии, экологичность
- Если клиент дает возражение — оператор его отрабатывает

Сгенерируй диалог в указанном формате.
"""
        return prompt

    def _call_yandex_gpt(self, prompt: str) -> str:
        """
        Отправляет запрос к Yandex GPT и возвращает сгенерированный диалог

        Args:
            prompt: промпт для генерации

        Returns:
            str: сгенерированный диалог
        """
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,  # Выше температура = больше креативности
                "maxTokens": "1000"
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Ты — генератор учебных диалогов для отдела продаж. Создавай реалистичные диалоги между клиентом и оператором. Используй только формат 'Клиент: ...' и 'Оператор: ...'."
                },
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                alternatives = result.get("result", {}).get("alternatives", [])
                if alternatives:
                    return alternatives[0].get("message", {}).get("text", "")
                return ""
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                return ""

        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
            return ""

    def _parse_dialog(self, text: str) -> List[Dict[str, str]]:
        """
        Парсит сгенерированный текст в структурированный диалог

        Args:
            text: текст с репликами в формате "Клиент: ..." и "Оператор: ..."

        Returns:
            List[Dict]: список реплик с ролями и текстом
        """
        dialog = []
        lines = text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('Клиент:'):
                dialog.append({
                    "role": "user",
                    "text": line.replace('Клиент:', '').strip()
                })
            elif line.startswith('Оператор:'):
                dialog.append({
                    "role": "assistant",
                    "text": line.replace('Оператор:', '').strip()
                })

        return dialog

    def generate_dialog(self, scenario: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Генерирует один диалог по сценарию

        Args:
            scenario: сценарий диалога

        Returns:
            Optional[Dict]: структурированный диалог или None
        """
        print(f"   🔄 Генерация диалога: {scenario.get('name')}")

        # Формируем промпт
        prompt = self._build_generation_prompt(scenario)

        # Вызываем API
        response = self._call_yandex_gpt(prompt)

        if not response:
            print(f"   ❌ Не удалось сгенерировать диалог")
            return None

        # Парсим ответ
        dialog = self._parse_dialog(response)

        if not dialog:
            print(f"   ⚠️ Диалог не распознан, сохраняем сырой текст")
            dialog = [{"role": "raw", "text": response}]

        # Формируем результат
        result = {
            "id": str(uuid.uuid4())[:8],
            "scenario_id": scenario.get("id"),
            "scenario_name": scenario.get("name"),
            "timestamp": datetime.now().isoformat(),
            "dialog": dialog,
            "raw_response": response,
            "metadata": {
                "client_objection": scenario.get("client_objection"),
                "operator_strategy": scenario.get("operator_strategy"),
                "expected_outcome": scenario.get("expected_outcome")
            }
        }

        print(f"   ✅ Сгенерировано {len(dialog)} реплик")
        return result

    def generate_batch(self, scenario_id: Optional[int] = None, count: int = 3) -> List[Dict[str, Any]]:
        """
        Генерирует пакет диалогов

        Args:
            scenario_id: ID сценария (если None — все сценарии)
            count: количество диалогов на сценарий

        Returns:
            List[Dict]: список сгенерированных диалогов
        """
        # Выбираем сценарии
        if scenario_id is not None:
            scenarios = [s for s in self.scenarios if s.get("id") == scenario_id]
        else:
            scenarios = self.scenarios

        if not scenarios:
            print("❌ Нет сценариев для генерации")
            return []

        results = []

        for scenario in scenarios:
            print(f"\n📋 Сценарий: {scenario.get('name')}")
            print(f"   Описание: {scenario.get('description')}")

            for i in range(count):
                print(f"\n   🔸 Диалог {i + 1}/{count}")
                dialog = self.generate_dialog(scenario)
                if dialog:
                    results.append(dialog)

                    # Сохраняем в файл
                    self._save_dialog(dialog)

        print(f"\n✅ Сгенерировано диалогов: {len(results)}")
        return results

    def _save_dialog(self, dialog: Dict[str, Any]) -> Path:
        """
        Сохраняет диалог в JSON-файл

        Args:
            dialog: структурированный диалог

        Returns:
            Path: путь к сохраненному файлу
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{timestamp}_{dialog['id']}.json"
        file_path = self.output_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(dialog, f, ensure_ascii=False, indent=2)

        print(f"   💾 Сохранен: {filename}")
        return file_path

    def get_generated_dialogs(self) -> List[Dict[str, Any]]:
        """Возвращает все сгенерированные диалоги"""
        dialogs = []
        for file_path in self.output_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    dialogs.append(json.load(f))
            except Exception as e:
                print(f"❌ Ошибка загрузки {file_path.name}: {e}")

        return dialogs


# Тестирование
if __name__ == "__main__":
    print("🧪 Тестирование DialogGenerator")
    print("=" * 60)

    generator = DialogGenerator()

    # Генерируем по 1 диалогу для каждого сценария
    print("\n🚀 Генерация диалогов по всем сценариям...")
    results = generator.generate_batch(count=1)  # по 1 диалогу на сценарий

    if results:
        print(f"\n✅ Сгенерировано {len(results)} диалогов")
        print(f"📁 Сохранены в: {generator.output_dir}")
    else:
        print("❌ Ничего не сгенерировано")