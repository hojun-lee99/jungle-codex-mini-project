import os
from pathlib import Path


class Config:
    BASE_DIR = Path(__file__).resolve().parent
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ai_academic_validator")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    OPENAI_API_URL = os.getenv(
        "OPENAI_API_URL",
        "https://api.openai.com/v1/chat/completions",
    )

    OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "kor+eng")
    OCR_MAX_PAGES = int(os.getenv("OCR_MAX_PAGES", "3"))
    OCR_BACKEND = os.getenv("OCR_BACKEND", "auto")
    OCR_PADDLE_LANGUAGE = os.getenv("OCR_PADDLE_LANGUAGE", "korean")

    AUTO_DELETE_ORIGINAL = os.getenv("AUTO_DELETE_ORIGINAL", "False").lower() == "true"
    RULES_FILE = BASE_DIR / "rules" / "rules.json"
