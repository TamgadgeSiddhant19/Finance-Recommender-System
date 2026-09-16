import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Union
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from app.recommendations.constants import (
    AUDIT_SCHEMA_VERSION,
    RECOMMENDATION_ENGINE_VERSION,
    RECOMMENDATION_POLICY_VERSION,
)


class RecommendationAudit(Base):
    """
    Immutable audit trail recording the complete deterministic decision trace
    of a generated financial recommendation.
    """
    __tablename__ = "recommendation_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    recommendation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    engine_version: Mapped[str] = mapped_column(String(50), default=RECOMMENDATION_ENGINE_VERSION, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(50), default=RECOMMENDATION_POLICY_VERSION, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(50), default=AUDIT_SCHEMA_VERSION, nullable=False)
    input_snapshot_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    decision_trace: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    data_provenance: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    validation_result: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="audit")


def _json_serial_default(obj: Any) -> Any:
    """Handles Decimal, Enum, and datetime serialization for hashing and JSON storage."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "value"):
        return obj.value
    if hasattr(obj, "dict"):
        return obj.dict()
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return str(obj)


def compute_input_snapshot_hash(profile: Any, goals: Sequence[Any]) -> str:
    """
    Computes a deterministic SHA-256 hash representing the input financial profile and goals.
    Never includes sensitive credentials or passwords.
    """
    profile_dict = {}
    if profile:
        for attr in [
            "age",
            "monthly_income",
            "monthly_expenses",
            "total_savings",
            "monthly_investment_capacity",
            "total_debt",
            "risk_tolerance",
            "investment_experience",
        ]:
            val = getattr(profile, attr, None) if not isinstance(profile, dict) else profile.get(attr)
            if hasattr(val, "value"):
                val = val.value
            elif isinstance(val, Decimal):
                val = str(val)
            profile_dict[attr] = val

    goals_list = []
    for g in goals:
        g_dict = {}
        for attr in ["goal_type", "target_amount", "current_amount", "target_years", "priority"]:
            val = getattr(g, attr, None) if not isinstance(g, dict) else g.get(attr)
            if hasattr(val, "value"):
                val = val.value
            elif isinstance(val, Decimal):
                val = str(val)
            g_dict[attr] = val
        goals_list.append(g_dict)

    canonical_payload = {
        "profile": profile_dict,
        "goals": sorted(goals_list, key=lambda x: (str(x.get("goal_type")), str(x.get("target_years")))),
    }

    serialized = json.dumps(canonical_payload, sort_keys=True, default=_json_serial_default)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
