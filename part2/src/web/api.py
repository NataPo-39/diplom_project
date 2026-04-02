"""
api.py - FastAPI сервер для ИИ-ассистента
Обрабатывает запросы от веб-интерфейса и возвращает ответы ассистента
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Добавляем путь к src для импорта
# Поднимаемся на 3 уровня вверх: api.py -> web -> src -> part2
PART2_ROOT = Path(__file__).parent.parent.parent
SRC_PATH = PART2_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
    print(f"✅ Добавлен путь: {SRC_PATH}")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Импортируем нашего ассистента
try:
    from assistant.core import CultConstructionsAssistant

    print("✅ Ассистент импортирован успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта ассистента: {e}")
    print(f"   Путь поиска: {sys.path}")
    raise

# Создаем экземпляр ассистента (один на все сессии)
# В реальном проекте нужно хранить состояние для каждого пользователя отдельно
# Но для прототипа так тоже работает
assistant = CultConstructionsAssistant()


# Модели данных для API
class ChatRequest(BaseModel):
    """Запрос от клиента"""
    message: str
    session_id: str = "default"  # для будущего разделения сессий


class ChatResponse(BaseModel):
    """Ответ ассистента"""
    response: str
    needs_human: bool
    collected_data: Dict[str, Any]


# Создаем FastAPI приложение
app = FastAPI(
    title="CULT CONSTRUCTIONS Assistant API",
    description="API для ИИ-ассистента компании CULT CONSTRUCTIONS",
    version="1.0.0"
)

# Настраиваем CORS (чтобы фронтенд мог обращаться к API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # в продакшене заменить на конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем статические файлы (HTML, CSS, JS)
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    print(f"✅ Статические файлы загружены из: {static_path}")
else:
    print(f"⚠️ Папка static не найдена: {static_path}")


@app.get("/")
async def root():
    """Главная страница - отдает index.html"""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "CULT CONSTRUCTIONS Assistant API работает"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Основной эндпоинт для общения с ассистентом
    Принимает сообщение пользователя, возвращает ответ ассистента
    """
    try:
        # Обрабатываем сообщение через нашего ассистента
        result = assistant.process_message(request.message)

        # Возвращаем результат
        return ChatResponse(
            response=result["response"],
            needs_human=result["needs_human"],
            collected_data=result["collected_data"]
        )
    except Exception as e:
        print(f"❌ Ошибка при обработке запроса: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    """Проверка работоспособности сервера"""
    return {
        "status": "healthy",
        "assistant_loaded": assistant is not None,
        "faq_count": len(assistant.knowledge_base.faq_data) if assistant else 0
    }


@app.post("/api/reset")
async def reset_session(session_id: str = "default"):
    """Сбрасывает диалог для указанной сессии"""
    assistant.reset_dialog()
    return {"status": "reset", "session_id": session_id}


if __name__ == "__main__":
    print("🚀 Запуск FastAPI сервера для ИИ-ассистента")
    print("=" * 60)
    print(f"📁 Статические файлы: {static_path}")
    print(f"📚 FAQ загружено: {len(assistant.knowledge_base.faq_data)} вопросов")
    print("\n🌐 Сервер будет запущен на порту 8001")
    print("\n🌐 Главная страница: http://localhost:8001")  # ← ДОБАВЬТЕ ЭТУ СТРОКУ
    print("📝 Документация API: http://localhost:8001/docs")
    print("=" * 60)

    print("🔄 Запускаю Uvicorn...")
    # Убираем reload=True для простоты
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001
    )