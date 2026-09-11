"""启动种子数据：默认租户、管理员、默认模型配置。"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.security import encrypt_secret, hash_password
from app.models.model_config import ModelConfig
from app.models.tenant import Tenant, User

logger = logging.getLogger("realframe.seed")

DEFAULT_ADMIN_EMAIL = "admin@realframe.local"
DEFAULT_ADMIN_PASSWORD = "admin123"

# 默认模型配置（API Key 留空，用户在「模型配置」界面填写）
DEFAULT_MODELS = [
    # task_type, provider, name, base_url, model, is_default
    ("chat", "openai_compat", "DeepSeek 文本", "https://api.deepseek.com", "deepseek-v4-flash", True),
    ("vision", "openai_compat", "DeepSeek 视觉", "https://api.deepseek.com", "deepseek-v4-flash-vision-exp", True),
    ("embed", "openai_compat", "智谱 Embedding", "https://open.bigmodel.cn/api/paas/v4", "embedding-3", True),
    ("image", "dashscope_image", "阿里通义万相", "https://dashscope.aliyuncs.com", "wan2.7-image-pro", True),
    ("chat", "openai_compat", "通义千问 文本", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen3.7-plus", False),
    ("chat", "openai_compat", "智谱 GLM 文本", "https://open.bigmodel.cn/api/paas/v4", "glm-5.3-flash", False),
    ("image", "dashscope_image", "通义万相 备选", "https://dashscope.aliyuncs.com", "qwen-image-3.0-pro", False),
]


def seed(db: Session) -> None:
    if db.query(Tenant).count() == 0:
        tenant = Tenant(name="默认租户", slug="default", plan="free", status="active")
        db.add(tenant)
        db.flush()

        admin = User(
            tenant_id=tenant.id,
            email=DEFAULT_ADMIN_EMAIL,
            name="管理员",
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            role="admin",
            is_superuser=True,
            status="active",
        )
        db.add(admin)
        logger.info("已创建默认租户与管理员 %s / %s", DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)
    else:
        tenant = db.query(Tenant).first()

    # 模型配置（按 provider+model+task_type 幂等）
    existing = {
        (m.provider, m.model, m.task_type): m
        for m in db.query(ModelConfig).filter(ModelConfig.tenant_id == tenant.id).all()
    }
    for task_type, provider, name, base_url, model, is_default in DEFAULT_MODELS:
        key = (provider, model, task_type)
        if key not in existing:
            db.add(
                ModelConfig(
                    tenant_id=tenant.id,
                    provider=provider,
                    name=name,
                    base_url=base_url,
                    api_key=encrypt_secret(""),
                    model=model,
                    task_type=task_type,
                    is_default=is_default,
                    enabled=True,
                )
            )
    db.commit()
