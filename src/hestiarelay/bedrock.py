from __future__ import annotations

import os
from typing import Any

import boto3

from hestiarelay.models import HouseholdState, PlanResult


class BedrockPlanner:
    def __init__(
        self,
        *,
        client: Any | None = None,
        model_id: str | None = None,
        region_name: str | None = None,
    ) -> None:
        self.model_id = model_id or os.getenv("HESTIA_BEDROCK_MODEL_ID")
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self.model_id)

    def _client_or_create(self) -> Any:
        if self._client is None:
            self._client = boto3.client("bedrock-runtime", region_name=self.region_name)
        return self._client

    def generate_plan(self, state: HouseholdState) -> PlanResult:
        if not self.configured:
            return PlanResult(
                source="deterministic",
                text=self._deterministic_plan(state),
                used_aws=False,
                model_id=None,
            )

        client = self._client_or_create()
        prompt = self._prompt(state)
        response = client.converse(
            modelId=self.model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 600, "temperature": 0.2},
        )
        content = response["output"]["message"]["content"]
        text = "\n".join(item["text"] for item in content if "text" in item).strip()
        return PlanResult(
            source="amazon-bedrock",
            text=text,
            used_aws=True,
            model_id=self.model_id,
        )

    @staticmethod
    def _prompt(state: HouseholdState) -> str:
        state_json = state.model_dump_json(indent=2)
        return (
            "You are HestiaRelay, a household continuity planning agent. "
            "Create a concise action plan using only low-risk planning actions. "
            "Do not claim to purchase, pay, delete, unlock, send messages, or mutate external "
            "accounts. Flag any such action as requiring explicit confirmation.\n\n"
            f"Household state:\n{state_json}"
        )

    @staticmethod
    def _deterministic_plan(state: HouseholdState) -> str:
        if not state.goal:
            return "Start by defining the household goal, date, people count, and optional budget."
        steps = [
            "Confirm guest constraints and household preferences.",
            "Build a preparation checklist ordered by deadline.",
            "Check the plan against the available budget.",
            "Surface any purchase or external-account action as a consent-gated proposal.",
        ]
        return "\n".join(f"{index}. {step}" for index, step in enumerate(steps, start=1))
