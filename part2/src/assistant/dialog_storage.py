"""
dialog_storage.py - Сохранение истории диалогов в JSON-файлы

Сохраняет:
- Полную историю сообщений
- Собранные данные о клиенте
- Временные метки
- Результат диалога (передан человеку или нет)
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


class DialogStorage:
    """
    Класс для сохранения истории диалогов в JSON-файлы
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Инициализация хранилища диалогов

        Args:
            storage_dir: путь к папке для сохранения файлов
        """
        # Определяем папку для хранения
        if storage_dir is None:
            # По умолчанию: part2/data/dialogs/
            self.storage_dir = Path(__file__).parent.parent.parent / "data" / "dialogs"
        else:
            self.storage_dir = Path(storage_dir)

        # Создаем папку, если её нет
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        print(f"📁 Хранилище диалогов: {self.storage_dir}")
        print(f"✅ DialogStorage инициализирован")

    def _generate_filename(self, session_id: str = None) -> Path:
        """
        Генерирует имя файла для сохранения диалога

        Args:
            session_id: идентификатор сессии (если есть)

        Returns:
            Path: полный путь к файлу
        """
        # Формат: YYYY-MM-DD_HH-MM-SS_[session_id].json
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        if session_id:
            filename = f"{timestamp}_{session_id}.json"
        else:
            # Если нет session_id, генерируем уникальный ID
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{timestamp}_{unique_id}.json"

        return self.storage_dir / filename

    def save_dialog(self,
                    dialog_history: List[Dict[str, Any]],
                    collected_data: Dict[str, Any],
                    session_id: str = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Path:
        """
        Сохраняет диалог в JSON-файл

        Args:
            dialog_history: история сообщений
            collected_data: собранные данные о клиенте
            session_id: идентификатор сессии
            metadata: дополнительная метаинформация

        Returns:
            Path: путь к сохраненному файлу
        """
        # Формируем структуру для сохранения
        dialog_data = {
            "session_id": session_id or str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "message_count": len(dialog_history),
            "dialog_history": dialog_history,
            "collected_data": collected_data,
            "metadata": metadata or {}
        }

        # Добавляем флаг "передан человеку" если есть телефон
        if collected_data.get("phone"):
            dialog_data["transferred_to_human"] = True
            dialog_data["transfer_reason"] = "phone_collected"
        else:
            dialog_data["transferred_to_human"] = False

        # Генерируем имя файла
        file_path = self._generate_filename(session_id)

        # Сохраняем в файл
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(dialog_data, f, ensure_ascii=False, indent=2)

            print(f"💾 Диалог сохранен: {file_path.name}")
            return file_path

        except Exception as e:
            print(f"❌ Ошибка сохранения диалога: {e}")
            raise

    def save_dialog_if_completed(self,
                                 dialog_history: List[Dict[str, Any]],
                                 collected_data: Dict[str, Any],
                                 session_id: str = None) -> Optional[Path]:
        """
        Сохраняет диалог только если он завершен (есть телефон или много сообщений)

        Args:
            dialog_history: история сообщений
            collected_data: собранные данные
            session_id: идентификатор сессии

        Returns:
            Optional[Path]: путь к файлу или None, если диалог не сохранен
        """
        # Сохраняем если:
        # 1. Есть телефон (клиент оставил контакты)
        # 2. Или диалог длинный (больше 6 сообщений)
        # 3. Или прошло много времени (но это сложнее, пока пропускаем)

        should_save = False
        reason = []

        if collected_data.get("phone"):
            should_save = True
            reason.append("phone_collected")

        if len(dialog_history) >= 8:  # 4+ сообщений от пользователя
            should_save = True
            reason.append("long_dialog")

        if should_save:
            metadata = {"save_reason": reason}
            return self.save_dialog(dialog_history, collected_data, session_id, metadata)

        return None

    def get_all_dialogs(self) -> List[Dict[str, Any]]:
        """
        Загружает все сохраненные диалоги

        Returns:
            List[Dict]: список всех диалогов
        """
        dialogs = []

        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    dialog = json.load(f)
                    dialogs.append(dialog)
            except Exception as e:
                print(f"❌ Ошибка загрузки {file_path.name}: {e}")

        # Сортируем по времени (новые сверху)
        dialogs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return dialogs

    def get_dialogs_by_date(self, date: str) -> List[Dict[str, Any]]:
        """
        Возвращает диалоги за указанную дату

        Args:
            date: дата в формате YYYY-MM-DD

        Returns:
            List[Dict]: список диалогов за дату
        """
        all_dialogs = self.get_all_dialogs()
        return [d for d in all_dialogs if d.get("date") == date]

    def get_dialogs_with_phone(self) -> List[Dict[str, Any]]:
        """
        Возвращает только диалоги, где есть телефон (лиды)

        Returns:
            List[Dict]: список диалогов-лидов
        """
        all_dialogs = self.get_all_dialogs()
        return [d for d in all_dialogs if d.get("collected_data", {}).get("phone")]


# Тестирование модуля
if __name__ == "__main__":
    print("🧪 Тестирование DialogStorage")
    print("=" * 60)

    # Создаем хранилище
    storage = DialogStorage()

    # Тестовые данные
    test_history = [
        {"role": "user", "text": "Здравствуйте! Сколько стоит забор?", "time": "2026-03-20T10:00:00"},
        {"role": "assistant", "text": "Здравствуйте! Для расчета нужна длина участка.", "time": "2026-03-20T10:00:05"},
        {"role": "user", "text": "У меня участок 30 метров", "time": "2026-03-20T10:00:15"},
        {"role": "assistant", "text": "Спасибо! Ориентировочная стоимость от 480 000 руб.",
         "time": "2026-03-20T10:00:20"},
        {"role": "user", "text": "Хочу оставить заявку, мой телефон +7 999 123-45-67", "time": "2026-03-20T10:00:30"},
    ]

    test_data = {
        "name": None,
        "phone": "+7 999 123-45-67",
        "email": None,
        "object_length": "30",
        "budget": None,
        "object_type": None,
        "needs_human": True
    }

    # Сохраняем тестовый диалог
    print("\n📝 Сохраняем тестовый диалог...")
    file_path = storage.save_dialog(test_history, test_data, session_id="test_session")
    print(f"✅ Сохранен в: {file_path}")

    # Проверяем сохранение только завершенных
    print("\n🔍 Проверка save_dialog_if_completed...")

    # Диалог без телефона (не должен сохраниться)
    short_dialog = [test_history[0], test_history[1]]
    no_phone_data = test_data.copy()
    no_phone_data["phone"] = None

    result = storage.save_dialog_if_completed(short_dialog, no_phone_data)
    if result is None:
        print("✅ Короткий диалог без телефона не сохранен (правильно)")

    # Диалог с телефоном (должен сохраниться)
    result = storage.save_dialog_if_completed(test_history, test_data)
    if result:
        print(f"✅ Диалог с телефоном сохранен: {result.name}")

    # Получаем все диалоги
    print("\n📊 Все сохраненные диалоги:")
    all_dialogs = storage.get_all_dialogs()
    for d in all_dialogs[:3]:  # покажем первые 3
        print(
            f"   - {d.get('date')} | {d.get('message_count')} сообщений | Телефон: {d.get('collected_data', {}).get('phone')}")

    print("\n" + "=" * 60)