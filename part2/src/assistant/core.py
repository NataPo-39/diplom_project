"""
core.py - Ядро ИИ-ассистента для компании CULT CONSTRUCTIONS
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
import uuid

# Исправляем пути
PART2_ROOT = Path(__file__).parent.parent.parent
SRC_PATH = PART2_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Импорты
try:
    from utils.config import config
    from assistant.knowledge_loader import KnowledgeBaseLoader
    from assistant.dialog_storage import DialogStorage
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"   Путь: {SRC_PATH}")
    sys.exit(1)



class CultConstructionsAssistant:
    """
    Основной класс ИИ-ассистента для компании CULT CONSTRUCTIONS
    """

    def __init__(self, knowledge_base_path: Optional[Path] = None):
        """
        Инициализация ассистента
        """
        # Загружаем конфигурацию
        self.api_key = config.get('yandex_api_key')
        self.folder_id = config.get('yandex_folder_id')
        self.model_uri = "gpt://b1gtp8bn97gg21fl5e9j/yandexgpt-5.1/latest"
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

        # Загружаем базу знаний
        print("📚 Загрузка базы знаний...")
        self.knowledge_base = KnowledgeBaseLoader(knowledge_base_path)

        # История диалога
        self.dialog_history: List[Dict[str, str]] = []
        self.max_history_length = 10

        # Данные, собранные от клиента
        self.collected_data = {
            "name": None,
            "phone": None,
            "email": None,
            "object_length": None,
            "budget": None,
            "object_type": None,
            "needs_human": False,
        }

        # Фразы-триггеры для передачи человеку
        self.human_triggers = [
            "свяжитесь со мной",
            "позвоните мне",
            "хочу поговорить со специалистом",
            "сложный вопрос",
            "индивидуальный расчет",
            "точная смета",
            "выезд специалиста",
        ]

        print(f"✅ Ассистент инициализирован")

        # Добавляем хранилище диалогов
        self.storage = DialogStorage()
        self.session_id = str(uuid.uuid4())[:8]  # уникальный ID сессии
        self.dialog_start_time = datetime.now()

    def _clean_markdown(self, text: str) -> str:
        """
        Удаляет маркдаун-разметку из текста для отображения в простом чате

        Args:
            text: исходный текст с возможной разметкой

        Returns:
            str: очищенный текст
        """
        if not text:
            return text

        # Удаляем **жирный текст**
        text = text.replace('**', '')

        # Удаляем *курсив*
        text = text.replace('*', '')

        # Удаляем `код`
        text = text.replace('`', '')

        # Удаляем # заголовки
        text = re.sub(r'^#+\s', '', text, flags=re.MULTILINE)

        # Удаляем маркдаун-списки (- или * в начале строки) и заменяем на bullet points
        text = re.sub(r'^\s*[-*]\s', '• ', text, flags=re.MULTILINE)

        # Удаляем маркдаун-ссылки [текст](ссылка) -> текст
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Удаляем множественные пробелы
        text = re.sub(r'\s+', ' ', text)

        # Удаляем пустые строки с точками
        text = re.sub(r'^\s*•\s*$', '', text, flags=re.MULTILINE)

        return text.strip()

    def _add_to_history(self, role: str, text: str) -> None:
        """Добавляет сообщение в историю диалога"""
        self.dialog_history.append({
            "role": role,
            "text": text,
            "time": datetime.now().isoformat()
        })

        if len(self.dialog_history) > self.max_history_length:
            self.dialog_history = self.dialog_history[-self.max_history_length:]

    def _extract_info_from_message(self, message: str) -> None:
        """Извлекает полезную информацию из сообщения"""
        message_lower = message.lower()

        # Упрощенный поиск телефона: ищем последовательности из 10-11 цифр
        phone_pattern = r'(\+7|8)?[\s\-]?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})'
        phone_match = re.search(phone_pattern, message)
        if phone_match and not self.collected_data["phone"]:
            self.collected_data["phone"] = phone_match.group()

        # Поиск длины
        length_pattern = r'(\d+)[\s]*(м|метр|метра|метров)'
        length_match = re.search(length_pattern, message_lower)
        if length_match and not self.collected_data["object_length"]:
            self.collected_data["object_length"] = length_match.group(1)

        # Поиск бюджета
        budget_pattern = r'(\d+)[\s]*(тыс|тысяч|млн|миллион)'
        budget_match = re.search(budget_pattern, message_lower)
        if budget_match and not self.collected_data["budget"]:
            self.collected_data["budget"] = budget_match.group()

        # Поиск имени (если есть фраза "меня зовут")
        name_pattern = r'(?:меня зовут|зовут|имя)\s+([А-ЯЁ][а-яё]+)'
        name_match = re.search(name_pattern, message_lower)
        if name_match and not self.collected_data["name"]:
            self.collected_data["name"] = name_match.group(1).capitalize()

        # Проверка на передачу человеку
        for trigger in self.human_triggers:
            if trigger in message_lower:
                self.collected_data["needs_human"] = True
                break

    def _check_if_ready_for_human(self) -> bool:
        """Проверяет, можно ли передать диалог человеку"""
        return bool(self.collected_data["phone"])

    def _format_history_for_prompt(self) -> str:
        """Форматирует историю для промпта"""
        if not self.dialog_history:
            return "История диалога пуста."

        formatted = "ИСТОРИЯ ДИАЛОГА:\n"
        for msg in self.dialog_history[-5:]:
            role = "Клиент" if msg["role"] == "user" else "Ассистент"
            formatted += f"{role}: {msg['text']}\n"
        return formatted

    def _build_prompt(self, user_message: str) -> List[Dict[str, str]]:
        """Формирует промпт для Yandex GPT"""
        system_prompt = self.knowledge_base.get_system_prompt()

        # Добавляем информацию о собранных данных
        if any(self.collected_data.values()):
            system_prompt += "\n\nСОБРАННАЯ ИНФОРМАЦИЯ О КЛИЕНТЕ:\n"
            if self.collected_data["name"]:
                system_prompt += f"- Имя: {self.collected_data['name']}\n"
            if self.collected_data["phone"]:
                system_prompt += f"- Телефон: {self.collected_data['phone']}\n"
            if self.collected_data["object_length"]:
                system_prompt += f"- Длина участка: {self.collected_data['object_length']} м\n"
            if self.collected_data["budget"]:
                system_prompt += f"- Бюджет: {self.collected_data['budget']}\n"

        # Добавляем историю диалога
        system_prompt += "\n" + self._format_history_for_prompt()

        # Формируем сообщения
        messages = [{"role": "system", "text": system_prompt}]
        messages.append({"role": "user", "text": user_message})

        return messages

    def process_message(self, user_message: str) -> Dict[str, Any]:
        """Обрабатывает сообщение пользователя"""
        self._add_to_history("user", user_message)
        self._extract_info_from_message(user_message)

        # БЛОК 1: Если есть телефон - передаем человеку
        if self._check_if_ready_for_human():
            response = self._generate_human_transfer_message()
            self._add_to_history("assistant", response)

            # Сохраняем диалог
            self.storage.save_dialog_if_completed(
                self.dialog_history,
                self.collected_data,
                self.session_id
            )

            return {
                "response": response,
                "needs_human": True,  # ← ЗДЕСЬ TRUE (передаем человеку)
                "collected_data": self.collected_data,
                "from_faq": False
            }

        # БЛОК 2: Обычный ответ (нет телефона)
        messages = self._build_prompt(user_message)
        assistant_response = self._call_yandex_gpt(messages)
        self._add_to_history("assistant", assistant_response)

        # Очищаем ответ от маркдауна
        cleaned_response = self._clean_markdown(assistant_response)

        # Сохраняем длинные диалоги
        if len(self.dialog_history) >= 8:
            self.storage.save_dialog_if_completed(
                self.dialog_history,
                self.collected_data,
                self.session_id
            )

        return {
            "response": cleaned_response,
            "needs_human": False,  # ← ЗДЕСЬ FALSE (обычный ответ)
            "collected_data": self.collected_data,
            "from_faq": False
        }

    def _generate_human_transfer_message(self) -> str:
        """Генерирует сообщение о передаче человеку"""
        name = self.collected_data.get("name", "")
        phone = self.collected_data.get("phone", "")

        if name and phone:
            message = (f"Спасибо, {name}! Я передал ваши контакты ({phone}) нашему специалисту. "
                       f"Он свяжется с вами в ближайшее время.")
        elif phone:
            message = (f"Спасибо! Я передал ваш телефон ({phone}) нашему специалисту. "
                       f"Он свяжется с вами в ближайшее время.")
        else:
            message = ("Спасибо за интерес! Для точного расчета оставьте ваш телефон, "
                       "и мы свяжемся с вами.")

        return self._clean_markdown(message)

    def _call_yandex_gpt(self, messages: List[Dict[str, str]]) -> str:
        """Отправляет запрос к Yandex GPT"""
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": "500"
            },
            "messages": messages
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                alternatives = result.get("result", {}).get("alternatives", [])
                if alternatives:
                    return alternatives[0].get("message", {}).get("text", "")
                return "Извините, не удалось получить ответ."
            else:
                return f"Извините, временная ошибка сервиса."

        except Exception:
            return "Извините, ошибка соединения."

    def get_collected_data(self) -> Dict:
        """Возвращает собранные данные"""
        return self.collected_data

    def reset_dialog(self) -> None:
        """Сбрасывает диалог"""
        self.dialog_history = []
        self.collected_data = {k: None for k in self.collected_data}
        self.collected_data["needs_human"] = False


# Тестирование
if __name__ == "__main__":
    print("🧪 Тестирование CultConstructionsAssistant")
    print("=" * 60)

    assistant = CultConstructionsAssistant()

    test_messages = [
        "Здравствуйте! Сколько стоит алюминиевый забор?",
        "У меня участок 30 метров",
        "А какой срок службы?",
        "Хочу оставить заявку, мой телефон +7 999 123-45-67"
    ]

    print("\n📋 Тестовый диалог:")
    print("-" * 40)

    for msg in test_messages:
        print(f"\n👤 Клиент: {msg}")
        result = assistant.process_message(msg)
        print(f"🤖 Ассистент: {result['response'][:100]}...")

        if result['needs_human']:
            print(f"👤 → Передача человеку!")
            print(f"📊 Данные: {result['collected_data']}")
            break

    print("\n" + "=" * 60)

    print("\n📚 Загрузка базы знаний...")
    print("✅ Ассистент инициализирован")
    print("✅ Класс создан успешно")