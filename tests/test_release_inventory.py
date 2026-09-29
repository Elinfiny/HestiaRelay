"""Exercise the actual collector with isolated files and no network or Docker effects."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("release_review", SCRIPTS / "release_review.py")
review_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review_module)
with patch.dict(sys.modules, {"release_review": review_module}):
    spec = importlib.util.spec_from_file_location(
        "inventory_under_test", SCRIPTS / "release_inventory.py"
    )
    inventory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inventory)


class ReleaseInventoryEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.previous = Path.cwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.previous)
        self.out = Path("qa-artifacts/release")
        self.out.mkdir(parents=True)
        Path("docs/evidence").mkdir(parents=True)
        Path("source.txt").write_text("owned fixture\n")
        self.surface = {"uid": 10001, "capabilities_zero": True}
        self.review = {
            "expires": "9999-12-31",
            "source_sha256": {"source.txt": hashlib.sha256(b"owned fixture\n").hexdigest()},
            "required_surface": self.surface.copy(),
            "findings": {"known": {"packages": {"package": "1"},
                                   "reason": "fixture", "reference": "NONLIVE"}},
        }
        self.finding = {"VulnerabilityID": "known", "PkgName": "package",
                        "InstalledVersion": "1", "Severity": "HIGH"}
        self.container = {"status": "PASS", "container_backup_restore": "PASS",
                          "image_id": "sha256:fixture"}
        self.calls = []
        self.output = io.StringIO()
        self.scanner = {"Version": "fixture", "VulnerabilityDB": {"Version": 2}}
        self.write_inputs()
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(inventory, "OUT", self.out))
        self.stack.enter_context(patch.object(inventory, "command", side_effect=self.command))
        self.stack.enter_context(patch.object(inventory.importlib.metadata, "distributions",
                                             return_value=[]))
        self.stack.enter_context(patch.object(inventory.urllib.request, "urlopen",
                                             side_effect=self.public_read))
        self.stack.enter_context(patch.dict(os.environ, {"HESTIA_SCAN_STATUSES": "0 " * 7 + "0",
                                                        "GITHUB_RUN_ID": "NONLIVE",
                                                        "GITHUB_RUN_ATTEMPT": "1"}))
        self.stack.enter_context(contextlib.redirect_stdout(self.output))

    def write_inputs(self):
        Path("docs/evidence/release-applicability.json").write_text(json.dumps(self.review))
        Path("qa-artifacts/container-qa.json").write_text(json.dumps(self.container))
        (self.out / "image-advisories.json").write_text(json.dumps({
            "Metadata": {"ImageID": "sha256:fixture"},
            "Results": [{"Vulnerabilities": [self.finding]}],
        }))
        (self.out / "scanner-version.json").write_text(json.dumps(self.scanner))

    @staticmethod
    @contextlib.contextmanager
    def public_read(*_args, **_kwargs):
        class Response:
            status = 200

            @staticmethod
            def read():
                return b"HestiaRelay MIT License"
        yield Response()

    def command(self, *args):
        self.calls.append(args)
        if args == ("git", "rev-parse", "HEAD"):
            return "NONLIVE-COMMIT"
        if args == ("git", "rev-list", "--all", "--count"):
            return "1"
        if args == ("git", "rev-parse", "--is-shallow-repository"):
            return "false"
        if args[:3] == ("docker", "image", "inspect"):
            return "sha256:fixture"
        if args[:2] == ("docker", "run"):
            self.assertIn("sha256:fixture", args)
            if "dpkg-query" in args:
                return "package\t1\tamd64"
            return json.dumps(self.surface if "platform.machine" in args[-1] else {})
        raise AssertionError(f"Unexpected external boundary: {args}")

    def assert_refusal(self, message):
        with self.assertRaisesRegex(AssertionError, message):
            inventory.main()
        self.assert_raw()
        for name in ["applicability.json", "audit-result.json", "sha256.json"]:
            self.assertFalse((self.out / name).exists(), name)
        self.assertEqual(self.output.getvalue(), "")

    def assert_raw(self):
        binding = json.loads((self.out / "evidence-binding.json").read_text())
        self.assertEqual(binding["evaluation"], "NOT_EVALUATED")
        self.assertEqual(binding["source_commit"], "NONLIVE-COMMIT")
        self.assertEqual(binding["scanner"], self.scanner)
        self.assertEqual(binding["image_id"], "sha256:fixture")
        self.assertEqual(binding["run_id"], "NONLIVE")
        self.assertEqual(binding["run_attempt"], "1")
        self.assertEqual(json.loads((self.out / "runtime-surface.json").read_text()), self.surface)
        for path, expected in binding["input_sha256"].items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), expected)

    def test_expired_retains_raw_only(self):
        self.review["expires"] = "2000-01-01"
        self.write_inputs()
        self.assert_refusal("expired")

    def test_source_drift_retains_raw_only(self):
        Path("source.txt").write_text("changed")
        self.assert_refusal("scope changed")

    def test_runtime_mismatch_retains_raw_only(self):
        self.surface["uid"] = 0
        self.assert_refusal("Runtime mitigation")

    def test_new_finding_refuses_before_success(self):
        self.finding["VulnerabilityID"] = "new"
        self.write_inputs()
        self.assert_refusal("Unresolved material")

    def test_critical_finding_refuses_before_success(self):
        self.finding["Severity"] = "CRITICAL"
        self.write_inputs()
        self.assert_refusal("Unresolved material")

    def test_container_mismatch_retains_raw_only(self):
        self.container["image_id"] = "different"
        self.write_inputs()
        self.assert_refusal("")

    def test_scanner_failure_refuses_before_success(self):
        os.environ["HESTIA_SCAN_STATUSES"] = "1 " + "0 " * 7
        self.assert_refusal("Scanner failure")

    def test_valid_path_and_duplicate_refusal(self):
        inventory.main()
        self.assert_raw()
        report = json.loads((self.out / "audit-result.json").read_text())
        self.assertEqual(report["scoped_applicability"]["blocking_findings"], [])
        self.assertEqual(len(report["scoped_applicability"]["scoped_decisions"]), 1)
        self.assertEqual(report["aws_calls"], 0)
        before = {p.name: p.read_bytes() for p in self.out.iterdir()}
        calls = len(self.calls)
        with self.assertRaisesRegex(AssertionError, "Stale inventory"):
            inventory.main()
        self.assertEqual(len(self.calls), calls)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.out.iterdir()})

    def test_failed_runtime_evidence_write_stops_review(self):
        actual = inventory.write_evidence

        def fail(path, value):
            if path.name == "runtime-surface.json":
                raise OSError("write refused")
            actual(path, value)

        with (
            patch.object(inventory, "write_evidence", side_effect=fail),
            patch.object(inventory, "review_findings") as review,
            self.assertRaisesRegex(OSError, "write refused"),
        ):
            inventory.main()
        review.assert_not_called()
        self.assertFalse((self.out / "audit-result.json").exists())

    def test_failed_binding_write_stops_review(self):
        actual = inventory.write_evidence

        def fail(path, value):
            if path.name == "evidence-binding.json":
                raise OSError("binding write refused")
            actual(path, value)

        with (
            patch.object(inventory, "write_evidence", side_effect=fail),
            patch.object(inventory, "review_findings") as review,
            self.assertRaises(OSError),
        ):
            inventory.main()
        review.assert_not_called()
        self.assertFalse((self.out / "audit-result.json").exists())

    def test_fsync_failure_stops_before_external_reads(self):
        with (
            patch.object(inventory.os, "fsync", side_effect=OSError("fsync")),
            self.assertRaises(OSError),
        ):
            inventory.main()
        self.assertEqual(self.calls, [("git", "rev-parse", "HEAD")])

    def test_readback_failure_stops(self):
        with (
            patch.object(Path, "read_bytes", return_value=b"partial"),
            self.assertRaisesRegex(AssertionError, "Evidence readback mismatch"),
        ):
            inventory.main()
        self.assertEqual(self.calls, [("git", "rev-parse", "HEAD")])

    def test_existing_claim_prevents_reentry(self):
        (self.out / "inventory-attempt.json").write_text("interrupted attempt")
        with self.assertRaises(FileExistsError):
            inventory.main()
        self.assertEqual(self.calls, [("git", "rev-parse", "HEAD")])

    def test_missing_scanner_input_stops_review(self):
        (self.out / "scanner-version.json").unlink()
        with (
            patch.object(inventory, "review_findings") as review,
            self.assertRaises(FileNotFoundError),
        ):
            inventory.main()
        review.assert_not_called()
        self.assertFalse((self.out / "audit-result.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
