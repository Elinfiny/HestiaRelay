from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class RiskLevel(StrEnum):
    SAFE = "safe"
    REVIEW = "review"
    PROTECTED = "protected"


class GoalStatus(StrEnum):
    ACTIVE = "active"
    READY = "ready"
    COMPLETE = "complete"


class ProposalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class HouseholdGoal(BaseModel):
    goal_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(min_length=3, max_length=240)
    when: str = Field(min_length=2, max_length=120)
    people: int = Field(ge=1, le=100)
    budget_usd: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    status: GoalStatus = GoalStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Preference(BaseModel):
    person: str = Field(min_length=1, max_length=120)
    note: str = Field(min_length=2, max_length=500)


class ActionProposal(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid4()))
    kind: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=3, max_length=500)
    risk: RiskLevel
    requires_confirmation: bool
    status: ProposalStatus = ProposalStatus.PENDING
    payload: dict[str, Any] = Field(default_factory=dict)
    context_hash: str | None = None
    execution: Literal["not_executed"] = "not_executed"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PlanResult(BaseModel):
    source: Literal["deterministic", "amazon-bedrock"]
    text: str
    used_aws: bool
    model_id: str | None = None
    fallback_reason: Literal["not_configured", "aws_unavailable"] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SessionRecord(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    number: int
    recovered_goal_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TurnRecord(BaseModel):
    request_id: str
    session_id: str
    user_text: str
    reply: str
    goal_id: str | None
    plan: PlanResult | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HouseholdState(BaseModel):
    goal: HouseholdGoal | None = None
    preferences: list[Preference] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    proposals: list[ActionProposal] = Field(default_factory=list)
    sessions: list[SessionRecord] = Field(default_factory=list)
    turns: list[TurnRecord] = Field(default_factory=list)
    plan: PlanResult | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
