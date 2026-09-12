from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError, NoCredentialsError

from hestiarelay.bedrock import BedrockPlanner
from hestiarelay.engine import HouseholdEngine
from hestiarelay.models import HouseholdState
from hestiarelay.service import CANONICAL_MESSAGES, HouseholdService
from hestiarelay.store import SQLiteStateStore


def make_service(path):
    planner = BedrockPlanner()
    planner.model_id = None
    return HouseholdService(HouseholdEngine(SQLiteStateStore(path)), planner)


def send(service, text):
    session = str(uuid4())
    service.new_session(session)
    return service.message(session_id=session, request_id=str(uuid4()), text=text)


def test_three_sessions_survive_recreation_and_preserve_goal_identity(tmp_path):
    path = tmp_path / "demo.db"
    first = send(make_service(path), CANONICAL_MESSAGES[0])
    second = send(make_service(path), CANONICAL_MESSAGES[1])
    third = send(make_service(path), CANONICAL_MESSAGES[2])
    goal_id = first["state"]["goal"]["goal_id"]
    assert second["state"]["goal"]["goal_id"] == goal_id
    state = third["state"]
    assert state["goal"]["goal_id"] == goal_id
    assert state["goal"]["people"] == 6
    assert state["goal"]["budget_usd"] == 120
    assert len({s["session_id"] for s in state["sessions"]}) == 3
    assert all(s["recovered_goal_id"] == goal_id for s in state["sessions"][1:])
    assert len(state["turns"]) == 3
    assert "allergic to nuts" in state["plan"]["text"]
    assert any("allergic to nuts" in task for task in state["checklist"])
    assert "Not ready yet" in state["turns"][-1]["reply"]
    assert state["proposals"][0]["status"] == "pending"
    assert state["proposals"][0]["risk"] == "protected"
    assert third["external_actions_performed"] == 0
    reopened = make_service(path).snapshot()
    assert reopened == third


def test_exact_proposal_decisions_persist_do_not_execute_or_broaden(tmp_path):
    service = make_service(tmp_path / "decisions.db")
    send(service, CANONICAL_MESSAGES[0])
    a = service.engine.propose_action(kind="purchase", description="One exact purchase")
    b = service.engine.propose_action(kind="calendar_write", description="One exact reminder")
    service.engine.propose_action(kind="new_unknown_kind", description="Unknown capability")
    service.engine.propose_action(kind="checklist", description="Local checklist")
    service.decide(action_id=a.action_id, approved=True)
    state = service.snapshot()["state"]
    assert [p["status"] for p in state["proposals"]] == [
        "approved",
        "pending",
        "pending",
        "pending",
    ]
    assert [p["risk"] for p in state["proposals"]] == ["protected", "review", "review", "safe"]
    service.decide(action_id=b.action_id, approved=False)
    service.decide(action_id=b.action_id, approved=False)
    with pytest.raises(ValueError, match="different final decision"):
        service.decide(action_id=b.action_id, approved=True)
    reopened = make_service(tmp_path / "decisions.db").snapshot()
    assert reopened["state"]["proposals"][1]["status"] == "rejected"
    assert all(p["execution"] == "not_executed" for p in reopened["state"]["proposals"])


def test_stale_context_requires_new_consent(tmp_path):
    service = make_service(tmp_path / "stale.db")
    send(service, CANONICAL_MESSAGES[0])
    send(service, CANONICAL_MESSAGES[2])
    proposal = service.engine.get_state().proposals[0]
    send(service, CANONICAL_MESSAGES[1])
    with pytest.raises(ValueError, match="Context changed"):
        service.decide(action_id=proposal.action_id, approved=True)
    service.decide(action_id=proposal.action_id, approved=False)
    send(service, CANONICAL_MESSAGES[2])
    assert len(service.engine.get_state().proposals) == 2


def test_duplicate_request_is_idempotent_and_conflicting_reuse_rejected(tmp_path):
    service = make_service(tmp_path / "replay.db")
    session, request = str(uuid4()), str(uuid4())
    service.new_session(session)
    service.new_session(session)
    args = {"session_id": session, "request_id": request, "text": CANONICAL_MESSAGES[0]}
    first = service.message(**args)
    assert service.message(**args) == first
    assert len(first["state"]["sessions"]) == 1
    with pytest.raises(ValueError, match="different message"):
        service.message(**(args | {"text": CANONICAL_MESSAGES[1]}))
    send(service, CANONICAL_MESSAGES[2])
    send(service, CANONICAL_MESSAGES[2])
    assert len(service.engine.get_state().proposals) == 1


@pytest.mark.parametrize(
    "text",
    [
        "",
        " " * 3,
        "x" * 501,
        "Buy it now",
        "Remember Ana is allergic to nuts.",
        "Are we ready for Friday?",
        "We're having zero people over Friday, budget $120.",
    ],
)
def test_invalid_or_missing_state_rolls_back_entire_turn(tmp_path, text):
    service = make_service(tmp_path / "invalid.db")
    session = str(uuid4())
    service.new_session(session)
    before = service.snapshot()
    with pytest.raises(ValueError):
        service.message(session_id=session, request_id=str(uuid4()), text=text)
    assert service.snapshot() == before


def test_missing_session_and_flexible_goal_values(tmp_path):
    service = make_service(tmp_path / "numbers.db")
    with pytest.raises(KeyError):
        service.message(session_id="missing", request_id="missing", text=CANONICAL_MESSAGES[0])
    result = send(service, "We're having 4 people over Saturday afternoon, budget $85.50.")
    assert result["state"]["goal"]["people"] == 4
    assert result["state"]["goal"]["budget_usd"] == 85.5
    assert result["state"]["goal"]["when"] == "Saturday afternoon"


def test_concurrent_writers_do_not_lose_preferences(tmp_path):
    path = tmp_path / "concurrent.db"
    make_service(path)

    def save(number):
        make_service(path).engine.remember_preference(person=f"Guest {number}", note="Vegetarian")

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(save, range(8)))
    assert len(make_service(path).engine.get_state().preferences) == 8


@pytest.mark.parametrize("response", [None, {}, {"output": {"message": {"content": []}}}])
def test_malformed_bedrock_response_degrades_explicitly(response):
    class Client:
        def converse(self, **kwargs):
            return response

    planner = BedrockPlanner(client=Client(), model_id="test-model")
    plan = planner.generate_plan(HouseholdState())
    assert plan.source == "deterministic"
    assert plan.used_aws is False
    assert plan.fallback_reason == "aws_unavailable"


@pytest.mark.parametrize(
    "error",
    [
        NoCredentialsError(),
        ClientError({"Error": {"Code": "AccessDenied", "Message": "PRIVATE_VALUE"}}, "Converse"),
    ],
)
def test_aws_failure_redacts_exception_and_persists_fallback(tmp_path, error):
    class Client:
        def converse(self, **kwargs):
            raise error

    service = make_service(tmp_path / "fallback.db")
    service.planner = BedrockPlanner(client=Client(), model_id="test-model")
    result = send(service, CANONICAL_MESSAGES[0])
    assert result["state"]["plan"]["fallback_reason"] == "aws_unavailable"
    assert "PRIVATE_VALUE" not in str(result)
    assert make_service(tmp_path / "fallback.db").engine.get_state().plan.source == "deterministic"


def test_bedrock_client_creation_and_mocked_provenance(tmp_path, monkeypatch):
    calls = []

    class Client:
        def converse(self, **kwargs):
            calls.append(kwargs)
            return {"output": {"message": {"content": [{"text": "Review the constraints."}]}}}

    def factory(name, **kwargs):
        assert name == "bedrock-runtime"
        assert kwargs["config"].read_timeout == 12
        return Client()

    monkeypatch.setattr("hestiarelay.bedrock.boto3.client", factory)
    service = make_service(tmp_path / "bedrock.db")
    service.planner = BedrockPlanner(model_id="mock-only")
    result = send(service, CANONICAL_MESSAGES[0])
    assert result["state"]["plan"]["source"] == "amazon-bedrock"
    assert result["state"]["turns"][0]["plan"]["used_aws"] is True
    assert len(calls) == 1
    assert "turns" not in calls[0]["messages"][0]["content"][0]["text"]


def test_old_sqlite_state_migrates_without_discard_and_reset_is_explicit(tmp_path):
    store = SQLiteStateStore(tmp_path / "old.db")
    with store.connection() as connection:
        connection.execute(
            "INSERT INTO household_state VALUES (1, ?)", ('{"checklist":["Keep me"]}',)
        )
    assert store.load().checklist == ["Keep me"]
    assert store.load().sessions == []
    store.reset()
    assert store.load().checklist == []
