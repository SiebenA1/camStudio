"""模型汇总导入（确保 Base.metadata 注册所有表）。"""
from app.models.base import Base
from app.models.tenant import Tenant, User, project_members
from app.models.project import (
    Project,
    Brief,
    Variable,
    VariableCombo,
    PromptTemplate,
)
from app.models.previz import PrevizAsset, GenerationTask
from app.models.reference import ReferenceShot
from app.models.equipment import EquipmentProfile
from app.models.review import Review, ReviewComment, ReviewVote, Approval
from app.models.model_config import ModelConfig, AuditLog

__all__ = [
    "Base",
    "Tenant",
    "User",
    "project_members",
    "Project",
    "Brief",
    "Variable",
    "VariableCombo",
    "PromptTemplate",
    "PrevizAsset",
    "GenerationTask",
    "ReferenceShot",
    "EquipmentProfile",
    "Review",
    "ReviewComment",
    "ReviewVote",
    "Approval",
    "ModelConfig",
    "AuditLog",
]
