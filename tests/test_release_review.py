"""Security-gate regressions: a scoped decision cannot conceal new vulnerability scope."""

import importlib.util
from datetime import date
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("release_review", Path("scripts/release_review.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def review():
    return {
        "expires": "2026-09-27",
        "source_sha256": {"source": "exact"},
        "required_surface": {"no_new_privileges": True},
        "findings": {
            "CVE-example": {
                "packages": {"package": "1"},
                "reason": "component absent",
                "reference": "vendor",
            }
        },
    }


def finding():
    return {
        "VulnerabilityID": "CVE-example",
        "PkgName": "package",
        "InstalledVersion": "1",
        "Severity": "HIGH",
    }


def run(item, **kwargs):
    return module.review_findings(
        [item],
        review(),
        kwargs.get("surface", {"no_new_privileges": True}),
        kwargs.get("hashes", {"source": "exact"}),
        kwargs.get("today", date(2026, 9, 13)),
    )


def test_exact_scoped_decision_retains_severity():
    result = run(finding())
    assert not result["blocking_findings"]
    assert result["scoped_decisions"][0]["scanner_severity"] == "HIGH"


@pytest.mark.parametrize(
    "change",
    [
        {"VulnerabilityID": "CVE-new"},
        {"InstalledVersion": "2"},
        {"PkgName": "different"},
        {"Severity": "CRITICAL"},
        {"FixedVersion": "2"},
    ],
)
def test_new_or_fixable_scope_cannot_inherit_decision(change):
    assert run(finding() | change)["blocking_findings"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"surface": {"no_new_privileges": False}},
        {"hashes": {"source": "changed"}},
        {"today": date(2026, 9, 28)},
    ],
)
def test_changed_controls_or_expired_review_fails_closed(kwargs):
    with pytest.raises(AssertionError):
        run(finding(), **kwargs)
