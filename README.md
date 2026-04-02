# Дипломный проект: Анализ телефонных переговоров и генерация синтетических диалогов на основе Yandex Cloud

## Описание проекта

Данный проект представляет собой прототип системы для автоматического анализа записей колл‑центра и создания синтетических диалогов с использованием российских облачных технологий (Yandex Cloud). Состоит из трёх частей:

1. **Транскрибация реальных звонков** – обработка низкокачественных MP3‑записей (предобработка, распознавание через синхронный API Yandex SpeechKit).
2. **ИИ-ассистент для сайта** – чат-бот на FastAPI с логикой диалога, сбором данных (телефон, длина участка), передачей специалисту и сохранением истории.
3. **Генерация и анализ синтетических диалогов** – создание сценариев, генерация диалогов через Yandex GPT, синтез речи (TTS), асинхронное распознавание (STT), экспорт в CSV и анализ в Google Sheets.

Проект выполнен в рамках дипломной работы. Все компоненты работают на российских облачных серверах, что соответствует требованиям Федерального закона № 152‑ФЗ «О персональных данных».

## Технологии

- **Язык:** Python 3.11+
- **Облачные сервисы:** Yandex Cloud (SpeechKit, GPT, Object Storage)
- **Веб-фреймворк:** FastAPI, Uvicorn
- **Обработка аудио:** PyDub, FFmpeg
- **Анализ данных:** Google Sheets (формулы), CSV
- **Контроль версий:** Git, GitHub

## Структура репозитория

```text
diplom_project/
├── part1/
│   ├── src/
│   │   └── services/
│   ├── scripts/
│   └── data/
├── part2/
│   ├── src/
│   │   ├── assistant/
│   │   ├── generator/
│   │   ├── tts/
│   │   ├── transcription/
│   │   ├── utils/
│   │   └── web/
│   │       └── static/
│   ├── data/
│   │   ├── knowledge_base/
│   │   ├── scenarios/
│   │   ├── generated/
│   │   │   ├── dialogs/
│   │   │   └── audio/
│   │   ├── transcriptions/
│   │   └── results/
│   └── scripts/
├── scripts/
├── tests/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```



## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/NataPo-39/diplom_project.git
cd diplom_project

2. Создание виртуального окружения

python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

3. Установка зависимостей

pip install -r requirements.txt

4. Настройка переменных окружения
Скопируйте .env.example в .env и заполните своими ключами:

cp .env.example .env   # Linux/Mac
copy .env.example .env # Windows

Отредактируйте .env, указав:

YANDEX_API_KEY и YANDEX_FOLDER_ID (из консоли Yandex Cloud)

AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BUCKET_NAME – для Object Storage (если планируете использовать асинхронную транскрибацию)

Опционально: VK_BOT_TOKEN, TELEGRAM_BOT_TOKEN – для уведомлений

5. Запуск первой части (транскрибация)
Поместите MP3‑файлы в part1/data/input/ и выполните:

python main.py

Результаты транскрибации появятся в part1/data/output/.

6. Запуск ИИ-ассистента (вторая часть)

cd part2
python src/web/api.py

Откройте в браузере http://localhost:8001. Чат готов к работе.

7. Генерация синтетических диалогов

cd part2
python -m src.generator.dialog_generator

Сгенерированные диалоги появятся в part2/data/generated/dialogs/. Для синтеза речи и транскрибации запустите соответствующие модули (tts_converter.py, async_transcriber.py).

Примеры работы
Скриншоты веб-чата и таблиц Google Sheets приведены в дипломной работе (файл docs/diplom.pdf).

Примеры сгенерированных диалогов – в part2/data/generated/dialogs/.

Лицензия
Проект разработан в рамках учебной дипломной работы. Использование кода допускается только в образовательных целях.


[Диплом (PDF)](docs/DIPLOM.pdf)


Контакты:
Автор: Наталья Пономаренко
GitHub: NataPo-39
