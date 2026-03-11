import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    APP_NAME = "WhatShouldI"
    SECRET_KEY = os.getenv("SECRET_KEY", "whatshouldi-dev-secret")
    DEBUG = _env_flag("FLASK_DEBUG", True)
    HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT = int(os.getenv("FLASK_PORT", "5000"))

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "whatshouldi")
    USE_MOCK_ON_FAILURE = _env_flag("USE_MOCK_ON_FAILURE", True)

    DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Seoul")
    DEFAULT_REGION = os.getenv("DEFAULT_REGION", "KR")
