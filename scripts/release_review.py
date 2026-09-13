"""Fail closed on new/changed findings; retain scoped, expiring applicability decisions."""

from datetime import date


def review_findings(findings, review, surface, source_hashes, today=None):
    today = today or date.today()
    assert today <= date.fromisoformat(review["expires"]), "Applicability review expired"
    assert source_hashes == review["source_sha256"], "Reviewed source or dependency scope changed"
    assert all(surface.get(key) == value for key, value in review["required_surface"].items()), (
        "Runtime mitigation or component absence was not demonstrated"
    )
    decisions, blocking = [], []
    for finding in findings:
        severity = finding.get("Severity", "UNKNOWN")
        if severity not in {"HIGH", "CRITICAL", "UNKNOWN"}:
            continue
        rule = review["findings"].get(finding["VulnerabilityID"])
        applicable = (
            severity != "CRITICAL"
            and not finding.get("FixedVersion")
            and rule
            and rule["packages"].get(finding["PkgName"]) == finding["InstalledVersion"]
        )
        if applicable:
            decisions.append(
                {
                    "id": finding["VulnerabilityID"],
                    "package": finding["PkgName"],
                    "version": finding["InstalledVersion"],
                    "scanner_severity": severity,
                    "decision": "NOT_REACHABLE_IN_REVIEWED_RUNTIME",
                    "reason": rule["reason"],
                    "reference": rule["reference"],
                }
            )
        else:
            blocking.append(finding)
    return {"scoped_decisions": decisions, "blocking_findings": blocking}
