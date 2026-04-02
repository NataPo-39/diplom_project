"""
export_to_csv.py - Экспорт диалогов и транскриптов в CSV для анализа в Google Sheets
"""

import sys
import json
import csv
from pathlib import Path
from typing import Dict, List, Any

# Добавляем путь к src для импорта (хотя здесь он не обязателен, оставим для единообразия)
PART2_ROOT = Path(__file__).parent.parent
SRC_PATH = PART2_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


def extract_full_text_from_dialog(dialog_data: Dict[str, Any]) -> str:
    """
    Извлекает полный текст диалога из JSON (склеивает реплики с указанием роли)
    """
    turns = dialog_data.get("dialog", [])
    if not turns:
        return ""

    lines = []
    for turn in turns:
        role = turn.get("role")
        text = turn.get("text", "").strip()
        if role == "user":
            lines.append(f"Клиент: {text}")
        elif role == "assistant":
            lines.append(f"Оператор: {text}")
        else:
            lines.append(text)  # на случай сырых данных

    return "\n".join(lines)


def main():
    # Папки с данными
    dialogs_dir = PART2_ROOT / "data" / "generated" / "dialogs"
    transcripts_dir = PART2_ROOT / "data" / "transcriptions"
    output_dir = PART2_ROOT / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Ищем все JSON-диалоги
    dialog_files = sorted(dialogs_dir.glob("*.json"))
    if not dialog_files:
        print("⚠️ Нет файлов диалогов в", dialogs_dir)
        return

    print(f"📁 Найдено диалогов: {len(dialog_files)}")

    # Собираем результаты
    rows = []

    for dialog_path in dialog_files:
        # Читаем диалог
        with open(dialog_path, 'r', encoding='utf-8') as f:
            dialog = json.load(f)

        dialog_id = dialog_path.stem
        scenario_name = dialog.get("scenario_name", "неизвестно")
        original_text = extract_full_text_from_dialog(dialog)

        # Ищем соответствующий транскрипт
        transcript_path = transcripts_dir / f"{dialog_id}_transcript.json"
        transcribed_text = ""
        if transcript_path.exists():
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript = json.load(f)
                transcribed_text = transcript.get("text", "")
        else:
            print(f"⚠️ Транскрипт не найден для {dialog_id}")

        rows.append({
            "dialog_id": dialog_id,
            "scenario_name": scenario_name,
            "original_text": original_text,
            "transcribed_text": transcribed_text
        })

    # Сохраняем CSV
    output_csv = output_dir / "dialog_comparison.csv"
    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        fieldnames = ["dialog_id", "scenario_name", "original_text", "transcribed_text"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ CSV сохранён: {output_csv}")
    print(f"   Всего записей: {len(rows)}")
    print("\n📊 Статистика по длине текстов:")
    for row in rows:
        orig_len = len(row["original_text"])
        trans_len = len(row["transcribed_text"])
        print(f"   {row['dialog_id']}: исходный {orig_len} симв., транскрипт {trans_len} симв.")


if __name__ == "__main__":
    main()