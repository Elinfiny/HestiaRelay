from __future__ import annotations

from pathlib import Path

import pytest

from hestiarelay.engine import HouseholdEngine
from hestiarelay.models import ProposalStatus, RiskLevel
from hestiarelay.store import SQLiteStateStore


def make_engine(tmp_path: Path) -> HouseholdEngine:
    return HouseholdEngine(SQLiteStateStore(tmp_path / "state.db"))


def test_goal_and_preference_persist_across_engine_instances(tmp_path: Path) -> None:
    engine = make_engine(tmp_path)
    engine.start_goal(title="Dinner for six", when="Friday evening", people=6, budget_usd=120)
    engine.remember_preference(person="Ana", note="Nut allergy")

    reopened = make_engine(tmp_path)
    state = reopened.get_state()

    assert state.goal is not None
    assert state.goal.people == 6
    assert state.goal.budget_usd == 120
    assert state.preferences[0].person == "Ana"
    assert "Nut allergy" in reopened.continuity_brief()


def test_duplicate_preference_is_not_added_twice(tmp_path: Path) -> None:
    engine = make_engine(tmp_path)
    engine.remember_preference(person="Ana", note="Nut allergy")
    engine.remember_preference(person="ana", note="nut allergy")

    assert len(engine.get_state().preferences) == 1


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("planning", RiskLevel.SAFE),
        ("calendar_write", RiskLevel.REVIEW),
        ("purchase", RiskLevel.PROTECTED),
        ("unknown_future_tool", RiskLevel.REVIEW),
    ],
)
def test_risk_classification(tmp_path: Path, kind: str, expected: RiskLevel) -> None:
    assert make_engine(tmp_path).classify_action(kind) == expected


def test_sensitive_proposal_requires_exact_confirmation(tmp_path: Path) -> None:
    engine = make_engine(tmp_path)
    proposal = engine.propose_action(
        kind="purchase",
        description="Buy groceries for Friday",
        payload={"estimated_total": 74.5},
    )

    assert proposal.risk == RiskLevel.PROTECTED
    assert proposal.requires_confirmation is True
    assert proposal.status == ProposalStatus.PENDING

    approved = engine.decide_proposal(action_id=proposal.action_id, approved=True)
    assert approved.status == ProposalStatus.APPROVED


def test_unknown_action_id_is_rejected(tmp_path: Path) -> None:
    engine = make_engine(tmp_path)
    with pytest.raises(KeyError):
        engine.decide_proposal(action_id="missing", approved=True)
