"""文件存储抽象：默认本地磁盘，接口对齐未来 S3/MinIO。"""
from __future__ import annotations

import base64
import mimetypes
import uuid
from pathlib import Path

import httpx

from app.config import settings

_EXT_BY_MIME = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "application/pdf": ".pdf",
    "application/octet-stream": ".bin",
}


def _ext_for(content_type: str | None, default: str = ".png") -> str:
    if not content_type:
        return default
    return _EXT_BY_MIME.get(content_type.split(";")[0].strip(), default)


def public_url(subdir: str, filename: str) -> str:
    return f"{settings.storage_base_url.rstrip('/')}/{subdir}/{filename}"


async def save_from_url(url: str, subdir: str = "previz") -> str:
    """下载远程图片到本地存储，返回可访问的 URL 路径。"""
    dest_dir = Path(settings.storage_dir) / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        content = resp.content
        ext = _ext_for(resp.headers.get("content-type"), ".png")
        filename = f"{uuid.uuid4().hex}{ext}"
        (dest_dir / filename).write_bytes(content)
    return public_url(subdir, filename)


def save_bytes(content: bytes, subdir: str, content_type: str | None = None) -> str:
    dest_dir = Path(settings.storage_dir) / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext = _ext_for(content_type, ".bin")
    filename = f"{uuid.uuid4().hex}{ext}"
    (dest_dir / filename).write_bytes(content)
    return public_url(subdir, filename)


def _local_path(url: str) -> Path | None:
    """把本地存储的 URL 还原为文件系统路径；非本地 URL 返回 None。"""
    base = settings.storage_base_url.rstrip("/")
    if url.startswith(base):
        rel = url[len(base):].lstrip("/")
        return Path(settings.storage_dir) / rel
    if url.startswith("/files/"):
        rel = url[len("/files/"):]
        return Path(settings.storage_dir) / rel
    return None


def local_path(url: str | None) -> Path | None:
    """公开接口：把存储 URL 还原为本地文件路径（非本地返回 None）。"""
    if not url:
        return None
    return _local_path(url)


def image_url_to_base64(url: str) -> str | None:
    """把本地存储的图片 URL 转成 base64 data URL（供远程模型读取）。

    远程模型（如万相/智谱）无法访问 localhost，因此必须内联图片内容。
    非本地文件或文件不存在时返回 None（调用方应回退为原始 URL）。
    """
    p = _local_path(url)
    if p is None or not p.exists():
        return None
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def delete_local_file(url: str | None) -> None:
    """删除本地存储的文件（尽力而为，文件不存在则忽略）。"""
    if not url:
        return
    p = _local_path(url)
    if p is not None:
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass
