"""OpenAI 兼容 Provider：chat / vision / embed。

覆盖国内多家：DeepSeek、通义千问(DashScope compatible-mode)、智谱 GLM、
Kimi/Moonshot、火山方舟(豆包) 等，均走 /chat/completions 与 /embeddings。
"""
from __future__ import annotations

import httpx

from app.ai.providers.base import BaseProvider, ProviderConfig
from app.config import settings
from app.core.errors import AppError


class OpenAICompatProvider(BaseProvider):
    name = "openai_compat"

    def _headers(self, cfg: ProviderConfig) -> dict:
        return {
            "Authorization": f"Bearer {cfg.api_key}",
            "Content-Type": "application/json",
        }

    async def _chat_completions(
        self,
        cfg: ProviderConfig,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        url = f"{cfg.base_url.rstrip('/')}/chat/completions"
        body: dict = {"model": cfg.model, "messages": messages, "temperature": temperature}
        if max_tokens:
            body["max_tokens"] = max_tokens
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=settings.model_request_timeout) as client:
                resp = await client.post(url, headers=self._headers(cfg), json=body)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise AppError(
                502, "model_error",
                f"模型接口返回 {e.response.status_code}：{e.response.text[:300]}",
            ) from e
        except httpx.HTTPError as e:
            raise AppError(502, "model_unreachable", f"无法连接模型接口：{e}") from e
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def chat(self, cfg: ProviderConfig, messages: list[dict], **kwargs) -> str:
        return await self._chat_completions(
            cfg,
            messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens"),
            json_mode=kwargs.get("json_mode", False),
        )

    async def vision(
        self, cfg: ProviderConfig, prompt: str, image_urls: list[str], **kwargs
    ) -> str:
        content: list[dict] = [{"type": "text", "text": prompt}]
        for url in image_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})
        messages = [{"role": "user", "content": content}]
        return await self._chat_completions(
            cfg,
            messages,
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens"),
            json_mode=kwargs.get("json_mode", False),
        )

    async def embed(self, cfg: ProviderConfig, texts: list[str], **kwargs) -> list[list[float]]:
        url = f"{cfg.base_url.rstrip('/')}/embeddings"
        body = {"model": cfg.model, "input": texts}
        try:
            async with httpx.AsyncClient(timeout=settings.model_request_timeout) as client:
                resp = await client.post(url, headers=self._headers(cfg), json=body)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise AppError(502, "model_error", f"模型接口返回 {e.response.status_code}：{e.response.text[:300]}") from e
        except httpx.HTTPError as e:
            raise AppError(502, "model_unreachable", f"无法连接模型接口：{e}") from e
        data = resp.json()
        items = sorted(data["data"], key=lambda d: d.get("index", 0))
        return [item["embedding"] for item in items]
