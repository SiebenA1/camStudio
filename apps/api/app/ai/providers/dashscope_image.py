"""阿里通义万相（DashScope）文生图/图生图 Provider —— Wan 2.7 异步任务接口。

- 文生图：只传 text
- 图生图（空镜参考图）：content 里同时传 {"text":...} 与 {"image": "<空镜图 URL>"}
接口参考：https://www.alibabacloud.com/help/en/model-studio/wan-image-generation-and-editing-api-reference
"""
from __future__ import annotations

import httpx

from app.ai.providers.base import BaseProvider, ProviderConfig
from app.config import settings
from app.core.errors import AppError

# Wan 2.7 异步：提交接口 + 查询接口
SUBMIT_PATH = "/api/v1/services/aigc/image-generation/generation"
TASK_PATH = "/api/v1/tasks/{task_id}"


class DashScopeImageProvider(BaseProvider):
    name = "dashscope_image"

    def _headers(self, cfg: ProviderConfig, async_mode: bool = True) -> dict:
        h = {
            "Authorization": f"Bearer {cfg.api_key}",
            "Content-Type": "application/json",
        }
        if async_mode:
            h["X-DashScope-Async"] = "enable"
        return h

    async def submit_image(self, cfg: ProviderConfig, prompt: str, **params) -> str:
        """提交文生图/图生图任务，返回外部任务 id。params 支持 ref_image_url。"""
        url = f"{cfg.base_url.rstrip('/')}{SUBMIT_PATH}"

        # Wan 2.7 采用 messages 结构
        content: list[dict] = [{"text": prompt}]
        ref_image = params.get("ref_image")  # 公网 URL 或 base64 data URL
        if ref_image:
            content.append({"image": ref_image})

        parameters: dict = {"watermark": False}
        if params.get("size"):
            parameters["size"] = params["size"]
        if params.get("n"):
            parameters["n"] = int(params["n"])
        if params.get("seed") is not None:
            parameters["seed"] = int(params["seed"])
        for k, v in (params.get("extra") or {}).items():
            parameters[k] = v

        body = {
            "model": cfg.model,
            "input": {"messages": [{"role": "user", "content": content}]},
            "parameters": parameters,
        }

        try:
            async with httpx.AsyncClient(timeout=settings.model_request_timeout) as client:
                resp = await client.post(url, headers=self._headers(cfg), json=body)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise AppError(502, "model_error", f"DashScope 返回 {e.response.status_code}：{e.response.text[:300]}") from e
        except httpx.HTTPError as e:
            raise AppError(502, "model_unreachable", f"无法连接 DashScope：{e}") from e

        data = resp.json()
        if data.get("code"):
            raise AppError(502, "model_error", f"DashScope 错误 {data.get('code')}: {data.get('message')}")
        task_id = (data.get("output") or {}).get("task_id")
        if not task_id:
            raise AppError(502, "model_error", f"DashScope 未返回 task_id: {str(data)[:300]}")
        return task_id

    async def poll_image(self, cfg: ProviderConfig, external_task_id: str) -> dict:
        url = f"{cfg.base_url.rstrip('/')}{TASK_PATH.format(task_id=external_task_id)}"
        try:
            async with httpx.AsyncClient(timeout=settings.model_request_timeout) as client:
                resp = await client.get(url, headers=self._headers(cfg, async_mode=False))
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise AppError(502, "model_error", f"DashScope 轮询返回 {e.response.status_code}：{e.response.text[:300]}") from e
        except httpx.HTTPError as e:
            raise AppError(502, "model_unreachable", f"无法连接 DashScope：{e}") from e

        data = resp.json()
        output = data.get("output") or {}
        status = (output.get("task_status") or "").upper()

        if status == "SUCCEEDED":
            image_urls: list[str] = []
            for choice in output.get("choices", []):
                for c in choice.get("message", {}).get("content", []):
                    if c.get("type") == "image" and c.get("image"):
                        image_urls.append(c["image"])
            return {"status": "succeeded", "image_urls": image_urls,
                    "usage": output.get("usage", {}), "raw": data}
        if status in ("FAILED", "CANCELED"):
            return {"status": "failed", "image_urls": [],
                    "error": output.get("message") or data.get("message") or status, "raw": data}
        # PENDING / RUNNING / UNKNOWN
        return {"status": "running", "image_urls": [], "raw": data}
