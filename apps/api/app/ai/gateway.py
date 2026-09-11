"""模型网关：解析配置 + 按任务类型路由到 Provider 适配器。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.providers.base import BaseProvider, ProviderConfig
from app.ai.providers.openai_compat import OpenAICompatProvider
from app.ai.providers.dashscope_image import DashScopeImageProvider
from app.core.errors import AppError
from app.core.security import decrypt_secret
from app.core.storage import image_url_to_base64
from app.models.model_config import ModelConfig

REGISTRY: dict[str, BaseProvider] = {
    OpenAICompatProvider.name: OpenAICompatProvider(),
    DashScopeImageProvider.name: DashScopeImageProvider(),
}

# 任务类型 → 使用的 Provider 能力方法
TASK_TO_METHOD = {
    "chat": "chat",
    "vision": "vision",
    "embed": "embed",
    "image": "image",
    "video": "video",
}


def list_providers() -> list[dict]:
    """可用 Provider 清单（供模型配置界面）。"""
    return [
        {
            "provider": "openai_compat",
            "label": "OpenAI 兼容（文本/视觉/向量）",
            "task_types": ["chat", "vision", "embed"],
            "description": "适用于 DeepSeek、通义千问、智谱 GLM、Kimi、豆包等 OpenAI 兼容接口",
            "example_base_url": "https://api.deepseek.com",
        },
        {
            "provider": "dashscope_image",
            "label": "阿里通义万相（文生图·异步）",
            "task_types": ["image"],
            "description": "DashScope 异步任务接口，提交后轮询取图",
            "example_base_url": "https://dashscope.aliyuncs.com",
        },
    ]


def to_provider_config(cfg: ModelConfig) -> ProviderConfig:
    return ProviderConfig(
        provider=cfg.provider,
        name=cfg.name,
        base_url=cfg.base_url,
        api_key=decrypt_secret(cfg.api_key),
        model=cfg.model,
        task_type=cfg.task_type,
        extra=cfg.extra or {},
    )


def require_provider_config(cfg: ModelConfig) -> ProviderConfig:
    """解析配置并校验 API Key 已填写。"""
    pc = to_provider_config(cfg)
    if not pc.api_key:
        raise AppError(
            400, "no_api_key", f"模型「{cfg.name}」尚未配置 API Key，请在「模型配置」界面填写"
        )
    return pc


def resolve_config(
    db: Session,
    tenant_id: str,
    task_type: str,
    model: str | None = None,
    provider: str | None = None,
) -> ModelConfig:
    q = db.query(ModelConfig).filter(
        ModelConfig.tenant_id == tenant_id,
        ModelConfig.task_type == task_type,
        ModelConfig.enabled.is_(True),
    )
    if model:
        q = q.filter(ModelConfig.model == model)
    if provider:
        q = q.filter(ModelConfig.provider == provider)
    cfg = q.order_by(ModelConfig.is_default.desc(), ModelConfig.updated_at.desc()).first()
    # 视觉能力回退：未配置 vision 模型时，回退到多模态文本模型（chat）
    if not cfg and task_type == "vision":
        cfg = (
            db.query(ModelConfig)
            .filter(
                ModelConfig.tenant_id == tenant_id,
                ModelConfig.task_type == "chat",
                ModelConfig.enabled.is_(True),
            )
            .order_by(ModelConfig.is_default.desc(), ModelConfig.updated_at.desc())
            .first()
        )
    if not cfg:
        raise AppError(
            400, "no_model_config", f"未配置 task_type={task_type} 的模型，请在「模型配置」界面添加"
        )
    return cfg


def get_provider(name: str) -> BaseProvider:
    if name not in REGISTRY:
        raise AppError(400, "unknown_provider", f"未知 Provider: {name}")
    return REGISTRY[name]


# ---- 同步能力 ----
async def chat(
    db: Session, tenant_id: str, messages: list[dict], model=None, provider=None, **kwargs
) -> str:
    cfg = resolve_config(db, tenant_id, "chat", model, provider)
    return await get_provider(cfg.provider).chat(require_provider_config(cfg), messages, **kwargs)


async def vision(
    db: Session,
    tenant_id: str,
    prompt: str,
    image_urls: list[str],
    model=None,
    provider=None,
    **kwargs,
) -> str:
    cfg = resolve_config(db, tenant_id, "vision", model, provider)
    # 本地图片转 base64 内联，否则远程视觉模型无法访问 localhost
    resolved = [image_url_to_base64(u) or u for u in image_urls]
    return await get_provider(cfg.provider).vision(
        require_provider_config(cfg), prompt, resolved, **kwargs
    )


async def embed(db: Session, tenant_id: str, texts: list[str], model=None, provider=None) -> list[list[float]]:
    cfg = resolve_config(db, tenant_id, "embed", model, provider)
    return await get_provider(cfg.provider).embed(require_provider_config(cfg), texts)


# ---- 异步能力 ----
async def submit_image(
    db: Session,
    tenant_id: str,
    prompt: str,
    model=None,
    provider=None,
    **params,
) -> tuple[str, str, str]:
    """提交文生图任务。返回 (provider, model, external_task_id)。"""
    cfg = resolve_config(db, tenant_id, "image", model, provider)
    ext_id = await get_provider(cfg.provider).submit_image(
        require_provider_config(cfg), prompt, **params
    )
    return cfg.provider, cfg.model, ext_id


async def poll_image(
    db: Session, tenant_id: str, provider: str, model: str, external_task_id: str
) -> dict:
    cfg = resolve_config(db, tenant_id, "image", model, provider)
    return await get_provider(cfg.provider).poll_image(
        require_provider_config(cfg), external_task_id
    )
