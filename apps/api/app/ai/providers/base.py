"""Provider 抽象基类。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ProviderConfig:
    """解密后的模型配置（供适配器使用）。"""

    provider: str
    name: str
    base_url: str
    api_key: str
    model: str
    task_type: str
    extra: dict = field(default_factory=dict)


class BaseProvider(ABC):
    """所有模型 Provider 的抽象接口。

    - 文本/视觉/向量：同步（单次 HTTP）。
    - 文生图/文生视频：异步（submit 返回外部任务 id，poll 取结果）。
    """

    name: str = "base"

    # ---- 同步能力 ----
    async def chat(self, cfg: ProviderConfig, messages: list[dict], **kwargs) -> str:
        raise NotImplementedError(f"{self.name} 不支持 chat")

    async def vision(
        self, cfg: ProviderConfig, prompt: str, image_urls: list[str], **kwargs
    ) -> str:
        raise NotImplementedError(f"{self.name} 不支持 vision")

    async def embed(self, cfg: ProviderConfig, texts: list[str], **kwargs) -> list[list[float]]:
        raise NotImplementedError(f"{self.name} 不支持 embed")

    # ---- 异步能力 ----
    async def submit_image(self, cfg: ProviderConfig, prompt: str, **params) -> str:
        """提交文生图任务，返回外部任务 id。"""
        raise NotImplementedError(f"{self.name} 不支持 image")

    async def poll_image(self, cfg: ProviderConfig, external_task_id: str) -> dict:
        """轮询文生图结果，返回 {status, image_urls, raw}。"""
        raise NotImplementedError(f"{self.name} 不支持 image")

    async def submit_video(
        self, cfg: ProviderConfig, image_url: str, prompt: str, **params
    ) -> str:
        raise NotImplementedError(f"{self.name} 不支持 video")

    async def poll_video(self, cfg: ProviderConfig, external_task_id: str) -> dict:
        raise NotImplementedError(f"{self.name} 不支持 video")
