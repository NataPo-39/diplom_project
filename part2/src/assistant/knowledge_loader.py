"""
knowledge_loader.py - Загрузка и обработка базы знаний для ИИ-ассистента

Модуль читает файлы:
- knowledge_base.2.md (общая информация о компании)
- faq.json (структурированные вопросы-ответы)

И предоставляет методы для получения контекста в промпты
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class KnowledgeBaseLoader:
    """
    Загрузчик базы знаний для ИИ-ассистента компании CULT CONSTRUCTIONS
    """

    def __init__(self, knowledge_base_path: Optional[Path] = None):
        """
        Инициализация загрузчика

        Args:
            knowledge_base_path: путь к папке с файлами базы знаний
        """
        # Определяем путь к папке knowledge_base
        if knowledge_base_path is None:
            # По умолчанию: part2/data/knowledge_base/
            self.base_path = Path(__file__).parent.parent.parent / "data" / "knowledge_base"
        else:
            self.base_path = Path(knowledge_base_path)

        # Убеждаемся, что папка существует
        if not self.base_path.exists():
            raise FileNotFoundError(f"Папка базы знаний не найдена: {self.base_path}")

        # Инициализируем структуры для хранения данных
        self.faq_data: List[Dict] = []  # данные из faq.json
        self.company_info: str = ""  # текст из knowledge_base.2.md
        self.faq_dict: Dict[str, str] = {}  # быстрый поиск по вопросам

        # Загружаем данные
        self._load_faq()
        self._load_company_info()

        print(f"✅ KnowledgeBaseLoader инициализирован")
        print(f"   📁 Путь: {self.base_path}")
        print(f"   📊 FAQ загружено: {len(self.faq_data)} вопросов")
        print(f"   📄 Company info: {len(self.company_info)} символов")

    def _load_faq(self) -> None:
        """
        Загружает и парсит файл faq.json
        """
        faq_file = self.base_path / "faq.json"

        if not faq_file.exists():
            print(f"⚠️ Файл faq.json не найден: {faq_file}")
            return

        try:
            with open(faq_file, 'r', encoding='utf-8') as f:
                self.faq_data = json.load(f)

            # Создаем словарь для быстрого поиска по вопросам
            for item in self.faq_data:
                # Основной вопрос
                question = item.get('question', '')
                answer = item.get('answer', '')

                if question and answer:
                    self.faq_dict[question.lower()] = answer

                # Альтернативные вопросы
                alt_questions = item.get('alternate_questions', [])
                for alt_q in alt_questions:
                    if alt_q and answer:
                        self.faq_dict[alt_q.lower()] = answer

        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга faq.json: {e}")
        except Exception as e:
            print(f"❌ Непредвиденная ошибка при загрузке FAQ: {e}")

    def _load_company_info(self) -> None:
        """
        Загружает файл knowledge_base.2.md (информация о компании)
        """
        # Проверяем возможные имена файла
        possible_names = [
            "knowledge_base.2.md",
            "knowledge_base.md",
            "company_info.md"
        ]

        md_file = None
        for name in possible_names:
            candidate = self.base_path / name
            if candidate.exists():
                md_file = candidate
                break

        if md_file is None:
            print(f"⚠️ Файл с информацией о компании не найден")
            print(f"   Искали: {[str(self.base_path / n) for n in possible_names]}")
            return

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                self.company_info = f.read()
        except Exception as e:
            print(f"❌ Ошибка загрузки файла компании: {e}")

    def get_system_prompt(self) -> str:
        """
        Формирует системный промпт для ассистента на основе базы знаний

        Returns:
            str: текст системного промпта
        """
        prompt_parts = []

        # Базовая роль
        prompt_parts.append("Ты — ИИ-ассистент компании CULT CONSTRUCTIONS.")
        prompt_parts.append(
            "Компания специализируется на производстве и установке премиальных алюминиевых ограждений (заборов).")
        prompt_parts.append("")

        # Информация о компании (если загружена)
        if self.company_info:
            prompt_parts.append("ИНФОРМАЦИЯ О КОМПАНИИ:")
            prompt_parts.append(self.company_info)
            prompt_parts.append("")

        # Инструкции по поведению
        prompt_parts.append("ПРАВИЛА РАБОТЫ:")
        prompt_parts.append("1. Отвечай вежливо, профессионально, на русском языке.")
        prompt_parts.append("2. Если вопрос есть в FAQ — используй точный ответ оттуда.")
        prompt_parts.append(
            "3. Если вопрос сложный или требует индивидуального расчета — предложи оставить контакты для связи со специалистом.")
        prompt_parts.append("4. Собирай информацию: длина участка, бюджет, тип объекта.")
        prompt_parts.append(
            "5. Не выдумывай цены — говори только ориентиры (от 16 000 руб/м² материалы, от 5 000 руб/м² монтаж).")
        prompt_parts.append("6. Если клиент готов оставить контакты — сохрани их и передай менеджеру.")
        prompt_parts.append("")

        # FAQ для быстрого доступа (только ключевые)
        prompt_parts.append("ЧАСТЫЕ ВОПРОСЫ И ОТВЕТЫ:")
        for item in self.faq_data[:5]:  # берем первые 5 для контекста
            q = item.get('question', '')
            a = item.get('answer', '')
            if q and a:
                # Сокращаем ответ для системного промпта
                short_answer = a[:150] + "..." if len(a) > 150 else a
                prompt_parts.append(f"В: {q}")
                prompt_parts.append(f"О: {short_answer}")
                prompt_parts.append("")

        return "\n".join(prompt_parts)

    def get_faq_answer(self, question: str) -> Optional[str]:
        """
        Быстрый поиск ответа на вопрос в FAQ

        Args:
            question: вопрос пользователя

        Returns:
            str: ответ из базы или None, если не найдено
        """
        question_lower = question.lower().strip()

        # Прямой поиск
        if question_lower in self.faq_dict:
            return self.faq_dict[question_lower]

        # Поиск по вхождению ключевых слов (упрощенный)
        for q, a in self.faq_dict.items():
            # Если вопрос пользователя содержит ключевые слова из FAQ
            if any(word in question_lower for word in q.split() if len(word) > 3):
                return a

        return None

    def get_all_faq(self) -> List[Dict]:
        """
        Возвращает все данные FAQ

        Returns:
            List[Dict]: список всех вопросов-ответов
        """
        return self.faq_data

    def get_company_info(self) -> str:
        """
        Возвращает информацию о компании

        Returns:
            str: текст из файла knowledge_base
        """
        return self.company_info

    def get_context_for_prompt(self, user_question: str) -> Tuple[str, bool]:
        """
        Получает контекст для промпта на основе вопроса пользователя

        Args:
            user_question: вопрос пользователя

        Returns:
            Tuple[str, bool]: (контекст, найден_ли_точный_ответ_в_faq)
        """
        # Сначала ищем точный ответ в FAQ
        exact_answer = self.get_faq_answer(user_question)
        if exact_answer:
            return f"На вопрос '{user_question}' в нашей базе есть ответ:\n{exact_answer}", True

        # Если точного ответа нет, возвращаем общий контекст
        context = f"""
Контекст разговора:
Пользователь спрашивает: {user_question}

Информация о компании:
{self.company_info[:500]}...  # первые 500 символов для контекста
"""
        return context, False


# Для тестирования модуля
if __name__ == "__main__":
    print("🧪 Тестирование KnowledgeBaseLoader")
    print("=" * 60)

    try:
        loader = KnowledgeBaseLoader()

        print("\n📋 Системный промпт (первые 500 символов):")
        print("-" * 40)
        prompt = loader.get_system_prompt()
        print(prompt[:500])
        print("...")

        print("\n🔍 Тест поиска в FAQ:")
        test_questions = [
            "сколько стоит забор",
            "гарантия на забор",
            "чем алюминий лучше стали",
            "как заказать замер"
        ]

        for q in test_questions:
            answer = loader.get_faq_answer(q)
            if answer:
                print(f"✅ '{q}' → найден ответ ({len(answer)} символов)")
            else:
                print(f"❌ '{q}' → ответ не найден")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

    print("\n" + "=" * 60)