from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
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
    budget_usd: float | None = Field(default=None, ge=0)
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HouseholdState(BaseModel):
    goal: HouseholdGoal | None = None
    preferences: list[Preference] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    proposals: list[ActionProposal] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PlanResult(BaseModel):
    source: str
    text: str
    used_aws: bool
    model_id: str | None = None
