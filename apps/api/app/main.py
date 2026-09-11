"""FastAPI 应用入口。"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config import settings
from app.core.errors import register_exception_handlers
from app.core.seed import seed
from app.database import SessionLocal, engine
from app.models import Base
from app.workers.worker import worker_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("realframe")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据目录
    Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.storage_dir).parent.mkdir(parents=True, exist_ok=True)

    # 建表 + 种子数据
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()

    # 启动后台生成 worker
    stop_event = asyncio.Event()
    worker_task = asyncio.create_task(worker_loop(stop_event))
    logger.info("RealFrame Studio API 已启动")
    yield
    stop_event.set()
    worker_task.cancel()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

register_exception_handlers(app)

# 开发阶段允许任意来源（鉴权走 Authorization 头，非 cookie）；生产请收紧为 settings.cors_origin_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    # 让前端能读到下载文件名
    expose_headers=["Content-Disposition"],
)

# 静态文件服务（生成图片 / 上传文件）—— 挂载前确保目录存在
Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=str(settings.storage_dir)), name="files")

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
