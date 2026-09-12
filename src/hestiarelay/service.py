"""Shared application boundary for MCP tools and the browser simulator."""

from __future__ import annotations

import re

from hestiarelay.bedrock import BedrockPlanner
from hestiarelay.engine import HouseholdEngine, context_hash
from hestiarelay.models import SessionRecord, TurnRecord

CANONICAL_MESSAGES = [
    "We’re having six people over Friday evening, budget $120.",
    "Remember Ana is allergic to nuts.",
    "Are we ready for Friday?",
]
NUMBERS = dict(
    zip(
        ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"],
        range(1, 11),
        strict=True,
    )
)


class HouseholdService:
    def __init__(self, engine: HouseholdEngine, planner: BedrockPlanner):
        self.engine = engine
        self.planner = planner

    def snapshot(self) -> dict:
        with self.engine.store.transaction():
            return self._snapshot()

    def _snapshot(self) -> dict:
        state = self.engine.get_state()
        return {
            "state": state.model_dump(mode="json"),
            "brief": self.engine.continuity_brief(),
            "simulation": True,
            "external_actions_performed": 0,
            "bedrock_configured": self.planner.configured,
            "canonical_messages": CANONICAL_MESSAGES,
            "context_hash": context_hash(state),
        }

    def new_session(self, session_id: str) -> dict:
        with self.engine.store.transaction():
            state = self.engine.get_state()
            if not any(s.session_id == session_id for s in state.sessions):
                state.sessions.append(
                    SessionRecord(
                        session_id=session_id,
                        number=len(state.sessions) + 1,
                        recovered_goal_id=state.goal.goal_id if state.goal else None,
                    )
                )
                self.engine._save(state)
            return self.snapshot()

    def generate_plan(self):
        with self.engine.store.transaction():
            state = self.engine.get_state()
            state.plan = self.planner.generate_plan(state)
            self.engine._save(state)
            return state.plan

    def message(self, *, session_id: str, request_id: str, text: str) -> dict:
        if not text.strip() or len(text) > 500:
            raise ValueError("Enter a message between 1 and 500 characters.")
        with self.engine.store.transaction():
            state = self.engine.get_state()
            if not any(s.session_id == session_id for s in state.sessions):
                raise KeyError("Start a session first.")
            for turn in state.turns:
                if turn.request_id == request_id:
                    if turn.session_id != session_id or turn.user_text != text:
                        raise ValueError("Request ID already used for a different message.")
                    return self.snapshot()
            reply = self._interpret(text)
            state = self.engine.get_state()
            state.turns.append(
                TurnRecord(
                    request_id=request_id,
                    session_id=session_id,
                    user_text=text,
                    reply=reply,
                    goal_id=state.goal.goal_id if state.goal else None,
                    plan=state.plan,
                )
            )
            self.engine._save(state)
            return self.snapshot()

    def _interpret(self, text: str) -> str:
        normalized = text.strip().replace("’", "'")
        goal = re.fullmatch(
            r"We're having (\w+) people over (.{2,100}?), budget \$(\d+(?:\.\d{1,2})?)\.?",
            normalized,
            re.IGNORECASE,
        )
        preference = re.fullmatch(
            r"Remember ([\w -]{1,80}?) is (.{2,400}?)\.?", normalized, re.IGNORECASE
        )
        if goal:
            count, when, budget = goal.groups()
            people = int(count) if count.isdecimal() else NUMBERS.get(count.casefold(), 0)
            state = self.engine.start_goal(
                title="Dinner together",
                when=when,
                people=people,
                budget_usd=float(budget),
            )
            self.generate_plan()
            return (
                f"Saved: {people} people, {when}, ${state.goal.budget_usd:.2f} budget. "
                "I prepared a local checklist. Come back in a new session; the goal will remain."
            )
        if preference:
            if not self.engine.get_state().goal:
                raise ValueError("Start a household goal before adding demo constraints.")
            person, note = preference.groups()
            self.engine.remember_preference(person=person, note=note)
            self.generate_plan()
            return (
                f"Recovered the existing goal. Remembered: {person} is {note}. "
                "The checklist and plan now include this constraint. Confirm ingredients and "
                "cross-contact with the guest; this is not an allergy-safety certification."
            )
        if re.fullmatch(r"Are we ready for (.{2,100})\?", normalized, re.IGNORECASE):
            state = self.engine.get_state()
            if not state.goal:
                raise ValueError("No active goal yet. Start with the first example.")
            self.generate_plan()
            current_hash = context_hash(state)
            if not any(
                p.kind == "purchase" and p.context_hash == current_hash for p in state.proposals
            ):
                self.engine.propose_action(
                    kind="purchase",
                    description="Illustrative grocery purchase for the saved dinner goal",
                    payload={
                        "goal_id": state.goal.goal_id,
                        "estimated_total_usd": 74.50,
                        "estimate_only": True,
                        "merchant": "None selected",
                        "items": ["Vegetables", "Rice", "Fruit", "Drinks"],
                        "constraints": [p.model_dump() for p in state.preferences],
                        "scope": "Consent record only. No merchant, account or payment call.",
                    },
                )
            return (
                f"{self.engine.continuity_brief()} Not ready yet: guest constraints, "
                "ingredients and preparation still need checking. A $74.50 illustrative "
                "grocery proposal is shown for your decision. Nothing has been purchased."
            )
        raise ValueError(
            "This guided simulator supports the three examples below, with changed guest "
            "counts, dates, budgets or preferences. It is not a general Alexa+ language model."
        )

    def decide(self, *, action_id: str, approved: bool) -> dict:
        with self.engine.store.transaction():
            self.engine.decide_proposal(action_id=action_id, approved=approved)
            return self.snapshot()
