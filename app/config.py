from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
IS_VERCEL = os.getenv("VERCEL") == "1"

DEFAULT_DATABASE_PATH = Path("/tmp/purchase_chief.db") if IS_VERCEL else BASE_DIR / "data" / "purchase_chief.db"
DEFAULT_UPLOADS_DIR = Path("/tmp/uploads") if IS_VERCEL else BASE_DIR / "data" / "uploads"


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    database_path: Path = Path(os.getenv("DATABASE_PATH", str(DEFAULT_DATABASE_PATH)))
    uploads_dir: Path = Path(os.getenv("UPLOADS_DIR", str(DEFAULT_UPLOADS_DIR)))
    max_history_messages: int = int(os.getenv("MAX_HISTORY_MESSAGES", "24"))
    max_knowledge_chunks: int = int(os.getenv("MAX_KNOWLEDGE_CHUNKS", "6"))


settings = Settings()
