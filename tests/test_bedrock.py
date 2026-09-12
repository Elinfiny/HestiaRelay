from __future__ import annotations

from hestiarelay.bedrock import BedrockPlanner
from hestiarelay.models import HouseholdGoal, HouseholdState


class FakeBedrockClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": (
                                "1. Confirm preferences.\n"
                                "2. Prepare checklist.\n"
                                "3. Gate purchase."
                            )
                        }
                    ]
                }
            }
        }


def test_unconfigured_bedrock_uses_explicit_deterministic_fallback() -> None:
    planner = BedrockPlanner(client=FakeBedrockClient(), model_id=None)
    planner.model_id = None
    state = HouseholdState(goal=HouseholdGoal(title="Dinner", when="Friday", people=6))

    result = planner.generate_plan(state)

    assert result.used_aws is False
    assert result.source == "deterministic"
    assert "consent-gated proposal" in result.text


def test_configured_bedrock_calls_converse_api() -> None:
    client = FakeBedrockClient()
    planner = BedrockPlanner(client=client, model_id="example.model-v1", region_name="us-east-1")
    state = HouseholdState(goal=HouseholdGoal(title="Dinner", when="Friday", people=6))

    result = planner.generate_plan(state)

    assert result.used_aws is True
    assert result.source == "amazon-bedrock"
    assert result.model_id == "example.model-v1"
    assert len(client.calls) == 1
    assert client.calls[0]["modelId"] == "example.model-v1"
    assert client.calls[0]["messages"][0]["role"] == "user"


def test_prompt_forbids_claiming_sensitive_side_effects() -> None:
    prompt = BedrockPlanner._prompt(HouseholdState())

    assert "Do not claim to purchase" in prompt
    assert "explicit confirmation" in prompt
