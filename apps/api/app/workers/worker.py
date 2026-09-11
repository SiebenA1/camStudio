"""后台生成任务 worker：轮询 DB 队列，处理文生图等异步任务。

MVP 用单进程 asyncio 循环；生产可替换为 Celery/arq + Redis。
"""
from __future__ import annotations

import asyncio
import logging
import time

from sqlalchemy.orm import Session

from app.ai import gateway
from app.core.storage import image_url_to_base64, save_from_url
from app.database import SessionLocal
from app.models.previz import GenerationTask, PrevizAsset, AssetStatus
from app.models.previz import GenerationStatus

logger = logging.getLogger("realframe.worker")

POLL_INTERVAL = 3.0       # 任务轮询间隔（秒）
IMAGE_POLL_INTERVAL = 4.0  # 图片生成结果轮询间隔（秒）
IMAGE_POLL_TIMEOUT = 300.0  # 图片生成总超时（秒）
IDLE_SLEEP = 2.0          # 队列空闲时的休眠


async def _process_image_task(db: Session, task: GenerationTask) -> None:
    params: dict = task.params or {}
    prompt = params.get("prompt", "")

    # 参考图：本地 URL 需转 base64 内联，否则远程模型无法访问 localhost
    ref_image = params.get("ref_image_url")
    if ref_image:
        b64 = image_url_to_base64(ref_image)
        if b64:
            ref_image = b64

    # 1) 提交任务
    provider, model, ext_id = await gateway.submit_image(
        db,
        task.tenant_id,
        prompt,
        model=task.model or None,
        provider=task.provider or None,
        size=params.get("size"),
        n=params.get("n", 1),
        seed=params.get("seed"),
        ref_image=ref_image,
        extra=params.get("extra", {}),
    )
    task.external_task_id = ext_id
    task.status = GenerationStatus.RUNNING.value
    task.attempts += 1
    db.commit()

    # 2) 轮询结果
    deadline = time.time() + IMAGE_POLL_TIMEOUT
    while time.time() < deadline:
        result = await gateway.poll_image(db, task.tenant_id, provider, model, ext_id)
        status = result.get("status")
        if status == "succeeded":
            image_urls = result.get("image_urls", [])
            saved = []
            for u in image_urls:
                try:
                    saved.append(await save_from_url(u, subdir="previz"))
                except Exception as e:  # 单张失败不阻塞
                    logger.warning("下载图片失败 %s: %s", u, e)
            task.status = GenerationStatus.SUCCEEDED.value
            task.result = {"image_urls": saved, "raw": result.get("raw")}
            task.finished_at = str(time.time())

            asset = db.get(PrevizAsset, task.asset_id) if task.asset_id else None
            if asset:
                asset.file_url = saved[0] if saved else None
                asset.status = AssetStatus.SUCCEEDED.value if saved else AssetStatus.FAILED.value
                if not saved:
                    asset.error = "下载图片失败"
                asset.thumbnail_url = saved[0] if saved else None
            db.commit()
            return

        if status == "failed":
            err = result.get("error", "生成失败")
            task.status = GenerationStatus.FAILED.value
            task.error = err
            task.finished_at = str(time.time())
            asset = db.get(PrevizAsset, task.asset_id) if task.asset_id else None
            if asset:
                asset.status = AssetStatus.FAILED.value
                asset.error = err
            db.commit()
            return

        await asyncio.sleep(IMAGE_POLL_INTERVAL)

    # 超时
    task.status = GenerationStatus.FAILED.value
    task.error = "生成超时"
    task.finished_at = str(time.time())
    asset = db.get(PrevizAsset, task.asset_id) if task.asset_id else None
    if asset:
        asset.status = AssetStatus.FAILED.value
        asset.error = "生成超时"
    db.commit()


async def _run_once() -> int:
    """处理一批排队任务，返回处理数量。"""
    db = SessionLocal()
    processed = 0
    try:
        tasks = (
            db.query(GenerationTask)
            .filter(GenerationTask.status == GenerationStatus.QUEUED.value)
            .order_by(GenerationTask.priority.desc(), GenerationTask.created_at.asc())
            .limit(5)
            .all()
        )
        for task in tasks:
            task.status = GenerationStatus.RUNNING.value
            task.started_at = str(time.time())
            db.commit()
            try:
                if task.task_type == "image":
                    await _process_image_task(db, task)
                else:
                    task.status = GenerationStatus.FAILED.value
                    task.error = f"暂不支持的任务类型: {task.task_type}"
                    db.commit()
            except Exception as e:  # 单任务失败不拖垮循环
                logger.exception("任务 %s 处理异常", task.id)
                task.status = GenerationStatus.FAILED.value
                task.error = str(e)
                task.finished_at = str(time.time())
                # 同步更新资产状态，避免资产永远停在 pending
                if task.asset_id:
                    asset = db.get(PrevizAsset, task.asset_id)
                    if asset:
                        asset.status = AssetStatus.FAILED.value
                        asset.error = str(e)
                db.commit()
            processed += 1
    finally:
        db.close()
    return processed


async def worker_loop(stop_event: asyncio.Event | None = None) -> None:
    """持续轮询队列（由应用 lifespan 启动）。"""
    logger.info("worker 启动")
    while True:
        if stop_event and stop_event.is_set():
            break
        try:
            n = await _run_once()
            if n == 0:
                await asyncio.sleep(IDLE_SLEEP)
            else:
                await asyncio.sleep(POLL_INTERVAL)
        except Exception:
            logger.exception("worker 循环异常")
            await asyncio.sleep(IDLE_SLEEP)
