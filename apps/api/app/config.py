"""应用配置（pydantic-settings）。所有配置可用环境变量 / .env 覆盖。"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api 目录（本文件位于 apps/api/app/config.py）
BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- 应用 ----
    app_name: str = "RealFrame Studio API"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 天

    # ---- 数据库（默认 SQLite，生产可切 PostgreSQL + pgvector）----
    database_url: str = f"sqlite:///{(BASE_DIR / 'data' / 'realframe.db').as_posix()}"

    # ---- 存储（默认本地磁盘，生产可切 S3/MinIO）----
    storage_dir: Path = BASE_DIR / "data" / "uploads"
    storage_base_url: str = "http://localhost:8787/files"

    # ---- CORS ----
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001"

    # ---- 模型网关 ----
    model_request_timeout: float = 120.0
    # 生成任务重试次数
    generation_max_retries: int = 2

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
