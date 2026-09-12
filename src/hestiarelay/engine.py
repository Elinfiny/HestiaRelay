from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from functools import wraps
from typing import Any

from hestiarelay.models import (
    ActionProposal,
    HouseholdGoal,
    HouseholdState,
    Preference,
    ProposalStatus,
    RiskLevel,
)
from hestiarelay.store import SQLiteStateStore

PROTECTED_KINDS = {
    "purchase",
    "payment",
    "money_transfer",
    "external_account_change",
    "delete_data",
    "unlock_door",
}

REVIEW_KINDS = {
    "calendar_write",
    "send_message",
    "external_reminder",
}

SAFE_KINDS = {
    "planning",
    "checklist",
    "local_reminder",
    "budget_analysis",
    "meal_plan",
}


def atomic(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self.store.transaction():
            return method(self, *args, **kwargs)

    return wrapped


def context_hash(state: HouseholdState) -> str:
    context = {
        "goal": state.goal.model_dump(mode="json") if state.goal else None,
        "preferences": [p.model_dump() for p in state.preferences],
    }
    return hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()


class HouseholdEngine:
    def __init__(self, store: SQLiteStateStore) -> None:
        self.store = store

    def _load(self) -> HouseholdState:
        return self.store.load()

    def _save(self, state: HouseholdState) -> HouseholdState:
        state.updated_at = datetime.now(UTC)
        self.store.save(state)
        return state

    @atomic
    def start_goal(
        self,
        *,
        title: str,
        when: str,
        people: int,
        budget_usd: float | None = None,
    ) -> HouseholdState:
        state = self._load()
        state.goal = HouseholdGoal(
            title=title,
            when=when,
            people=people,
            budget_usd=budget_usd,
        )
        state.checklist = [
            "Confirm guest constraints",
            "Create preparation checklist",
            "Review budget before sensitive actions",
        ]
        state.plan = None
        return self._save(state)

    @atomic
    def remember_preference(self, *, person: str, note: str) -> HouseholdState:
        state = self._load()
        preference = Preference(person=person, note=note)
        duplicate = any(
            item.person.casefold() == preference.person.casefold()
            and item.note.casefold() == preference.note.casefold()
            for item in state.preferences
        )
        if not duplicate:
            state.preferences.append(preference)
            state.checklist.append(f"Verify with {preference.person}: {preference.note}")
            state.plan = None
        return self._save(state)

    def get_state(self) -> HouseholdState:
        return self._load()

    def continuity_brief(self) -> str:
        state = self._load()
        if not state.goal:
            return "No active household goal."

        budget = f"${state.goal.budget_usd:.2f}" if state.goal.budget_usd is not None else "not set"
        preferences = (
            "; ".join(f"{item.person}: {item.note}" for item in state.preferences)
            or "none recorded"
        )
        pending = [item for item in state.proposals if item.status == ProposalStatus.PENDING]
        return (
            f"Goal: {state.goal.title}. When: {state.goal.when}. "
            f"People: {state.goal.people}. Budget: {budget}. "
            f"Preferences: {preferences}. Pending approvals: {len(pending)}."
        )

    def classify_action(self, kind: str) -> RiskLevel:
        normalized = kind.strip().casefold()
        if normalized in PROTECTED_KINDS:
            return RiskLevel.PROTECTED
        if normalized in REVIEW_KINDS:
            return RiskLevel.REVIEW
        if normalized in SAFE_KINDS:
            return RiskLevel.SAFE
        return RiskLevel.REVIEW

    @atomic
    def propose_action(
        self,
        *,
        kind: str,
        description: str,
        payload: dict[str, Any] | None = None,
    ) -> ActionProposal:
        state = self._load()
        risk = self.classify_action(kind)
        proposal = ActionProposal(
            kind=kind.strip().casefold(),
            description=description,
            risk=risk,
            requires_confirmation=risk in {RiskLevel.REVIEW, RiskLevel.PROTECTED},
            payload=payload or {},
            context_hash=context_hash(state),
        )
        state.proposals.append(proposal)
        self._save(state)
        return proposal

    @atomic
    def decide_proposal(self, *, action_id: str, approved: bool) -> ActionProposal:
        state = self._load()
        for proposal in state.proposals:
            if proposal.action_id != action_id:
                continue
            if proposal.status != ProposalStatus.PENDING:
                expected = ProposalStatus.APPROVED if approved else ProposalStatus.REJECTED
                if proposal.status != expected:
                    raise ValueError("This proposal already has a different final decision.")
                return proposal
            if approved and proposal.context_hash != context_hash(state):
                raise ValueError("Context changed. Reject this proposal and request a new one.")
            proposal.status = ProposalStatus.APPROVED if approved else ProposalStatus.REJECTED
            self._save(state)
            return proposal
        raise KeyError(f"Unknown action_id: {action_id}")
