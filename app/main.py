from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import BASE_DIR, settings
from .db import init_db
from .deepseek_client import DeepSeekError, chat_completion
from .knowledge import chunk_text, extract_text_from_file, format_knowledge_context
from .prompts import PURCHASE_CHIEF_SYSTEM_PROMPT
from .repository import (
    add_knowledge_chunks,
    add_message,
    create_chat,
    create_document,
    get_chat,
    get_recent_messages,
    list_chats,
    list_documents,
    list_messages,
    search_knowledge,
)
from .schemas import (
    AttachmentResponse,
    ChatCreateRequest,
    ChatMessageReply,
    ChatResponse,
    MessageRequest,
    MessageResponse,
)

APP_VERSION = "1.1.0"

api_app = FastAPI(title="Purchase AI Chief API", version=APP_VERSION)

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api_app.on_event("startup")
def startup_api_event() -> None:
    init_db()


def _require_chat(chat_id: str) -> dict:
    chat = get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@api_app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": settings.deepseek_model}


@api_app.get("/chats", response_model=list[ChatResponse])
def get_chats() -> list[dict]:
    return list_chats()


@api_app.post("/chats", response_model=ChatResponse)
def post_chat(payload: ChatCreateRequest | None = None) -> dict:
    title = payload.title if payload else None
    chat = create_chat(title)
    chat["message_count"] = 0
    return chat


@api_app.get("/chats/{chat_id}/messages", response_model=list[MessageResponse])
def get_chat_messages(chat_id: str) -> list[dict]:
    _require_chat(chat_id)
    return list_messages(chat_id)


@api_app.get("/chats/{chat_id}/attachments", response_model=list[AttachmentResponse])
def get_attachments(chat_id: str) -> list[dict]:
    _require_chat(chat_id)
    return list_documents(chat_id)


@api_app.post("/chats/{chat_id}/attachments")
async def upload_attachment(chat_id: str, file: UploadFile = File(...)) -> dict:
    _require_chat(chat_id)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(raw) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File is too large. Max 25 MB")

    chat_upload_dir = settings.uploads_dir / chat_id
    chat_upload_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename).suffix.lower()
    stored_name = f"{uuid4().hex}{suffix}"
    stored_path = chat_upload_dir / stored_name
    stored_path.write_bytes(raw)

    try:
        extracted_text = extract_text_from_file(stored_path)
    except ValueError as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Could not parse file: {exc}") from exc

    if not extracted_text.strip():
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="No readable text found in attachment")

    document = create_document(
        chat_id=chat_id,
        original_name=file.filename,
        stored_path=str(stored_path),
        mime_type=file.content_type or "application/octet-stream",
        char_count=len(extracted_text),
    )

    chunks = chunk_text(extracted_text)
    document["chunk_count"] = add_knowledge_chunks(chat_id, document["id"], chunks)

    return document


@api_app.post("/chats/{chat_id}/messages", response_model=ChatMessageReply)
def post_message(chat_id: str, payload: MessageRequest) -> dict:
    _require_chat(chat_id)

    user_text = payload.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    user_message = add_message(chat_id, "user", user_text)
    history = get_recent_messages(chat_id, settings.max_history_messages)

    knowledge_hits = []
    if payload.use_knowledge:
        knowledge_hits = search_knowledge(chat_id, user_text, settings.max_knowledge_chunks)

    model_messages = [{"role": "system", "content": PURCHASE_CHIEF_SYSTEM_PROMPT}]

    knowledge_context = format_knowledge_context(knowledge_hits)
    if knowledge_context:
        model_messages.append({"role": "system", "content": knowledge_context})

    for item in history:
        model_messages.append({"role": item["role"], "content": item["content"]})

    try:
        assistant_text = chat_completion(model_messages)
    except DeepSeekError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not assistant_text:
        assistant_text = "I could not generate a response. Please retry."

    assistant_message = add_message(chat_id, "assistant", assistant_text)

    return {
        "chat_id": chat_id,
        "user_message": user_message,
        "assistant_message": assistant_message,
        "knowledge_hits": len(knowledge_hits),
    }


web_app = FastAPI(title="Purchase AI Chief", version=APP_VERSION)
STATIC_DIR = BASE_DIR / "static"
web_app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@web_app.on_event("startup")
def startup_web_event() -> None:
    init_db()


@web_app.get("/", response_class=FileResponse)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


web_app.mount("/api", api_app)

# Local entrypoint for uvicorn
app = web_app
