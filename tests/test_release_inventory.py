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
        self.npm_source_inputs = {
            name: (SCRIPTS.parent / name).read_bytes()
            for name in ("tools/inspector/package.json", "tools/inspector/package-lock.json")
        }
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
                          "image_id": "sha256:fixture",
                          "mcp_inspector": inventory.INSPECTOR_IDENTITY.copy()}
        self.calls = []
        self.output = io.StringIO()
        self.scanner = {"Version": "fixture", "VulnerabilityDB": {"Version": 2}}
        self.write_inputs()
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(inventory, "OUT", self.out))
        self.stack.enter_context(patch.object(inventory, "command", side_effect=self.command))
        # Existing collector fixtures are synthetic; they do not claim an installed CLI.
        self.stack.enter_context(patch.object(inventory, "inspector_audit_identity",
                                             return_value=inventory.INSPECTOR_IDENTITY.copy()))
        self.stack.enter_context(patch.object(inventory.importlib.metadata, "distributions",
                                             return_value=[]))
        self.stack.enter_context(patch.object(inventory.urllib.request, "urlopen",
                                             side_effect=self.public_read))
        self.stack.enter_context(patch.dict(os.environ, {"HESTIA_SCAN_STATUSES": "0 " * 7 + "0",
                                                        "HESTIA_NPM_BINDING_STATUS": "0",
                                                        "GITHUB_RUN_ID": "NONLIVE",
                                                        "GITHUB_RUN_ATTEMPT": "1"}))
        self.stack.enter_context(contextlib.redirect_stdout(self.output))

    def write_inputs(self):
        for name, data in self.npm_source_inputs.items():
            target = Path(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        Path("qa-artifacts/inspector-package-lock.json").write_bytes(
            self.npm_source_inputs["tools/inspector/package-lock.json"]
        )
        (self.out / "artifact-secrets.json").write_text("[]")
        (self.out / "npm-advisories.json").write_text(json.dumps({
            "auditReportVersion": 2, "vulnerabilities": {},
            "metadata": {"vulnerabilities":
                         {k: 0 for k in ("info", "low", "moderate", "high", "critical", "total")}},
        }))
        (self.out / "npm-audit-binding.json").write_text(json.dumps({
            "schema": 1, "status": "PASS", "prefix": "tools/inspector",
            "source_commit": "NONLIVE-COMMIT", "run_id": "NONLIVE", "run_attempt": "1",
            "input_sha256": inventory.NPM_INPUT_SHA256,
            "installed_inspector": inventory.INSPECTOR_IDENTITY,
        }))
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


class ExactArtifactDispositionTests(unittest.TestCase):
    # Optional immutable report bytes supplied by the private review harness as data only.
    historical_fixture = None

    def fixture(self):
        source = (SCRIPTS.parent / "src/hestiarelay/access.py").read_bytes()
        binding = {
            "source_commit": "d3f15f3fa4347dc781e43479282c6372d80ddbc0",
            "run_id": "38654133953", "run_attempt": "1",
            "image_id": "sha256:3822edaa512111b3ad3d2d64cd80d584ef59992a21d9c4f3c95d85e38811abfe",
            "scanner_image_id":
                "sha256:3822edaa512111b3ad3d2d64cd80d584ef59992a21d9c4f3c95d85e38811abfe",
            "source_sha256": {"src/hestiarelay/access.py": inventory.PUBLIC_ACCESS_SHA256},
        }
        container = {
            "source_commit": binding["source_commit"], "image_id": binding["image_id"],
            "dependency_lock_sha256": "d" * 64,
        }
        native = {
            "schema": "HESTIA_NATIVE_SURFACE_OBSERVATION_V1",
            "binding": {k: binding[k] for k in
                        ("source_commit", "run_id", "run_attempt", "image_id")},
            "image_source_sha256":
                {"/app/src/hestiarelay/access.py": inventory.PUBLIC_ACCESS_SHA256},
            "image_runtime_lock_sha256": "d" * 64,
            "files": [""],
        }
        native["binding"].update(
            primary_qa_error=None,
            probe_sha256="642530112b7fdfc79689d06509be8623b2a25b22874577de10ebffed8383cdfa",
            source_sha256={"tools/inspector/package-lock.json":
                           inventory.NPM_INPUT_SHA256["tools/inspector/package-lock.json"]},
        )

        def encode():
            return json.dumps(native, sort_keys=True, separators=(",", ":")).encode()

        # Inert padding reproduces the reviewed coordinate, without invoking a native probe.
        prefix = encode().index(b'access.py":"')
        native["files"] = ["x" * (55790 - prefix)]
        member = encode()
        report = json.dumps([inventory.REVIEWED_ARTIFACT_FINDING]).encode()
        return [report, 1, member, source, binding, container]

    def classify(self, args):
        return inventory.classify_artifact_findings(*args)

    def test_exact_public_hash_binding_disposition(self):
        args = self.fixture()
        result = self.classify(args)
        self.assertFalse(result["blocking"], result)
        self.assertEqual(result["raw_scanner_status"], 1)
        self.assertEqual(result["accepted_count"], 1)
        self.assertFalse(result["universal_secret_absence"])
        self.assertEqual(json.loads(args[0]), [inventory.REVIEWED_ARTIFACT_FINDING])
        if self.historical_fixture is not None:
            actual = self.classify(self.historical_fixture)
            self.assertFalse(actual["blocking"], actual)
            self.assertEqual(actual["source_sha256"], inventory.PUBLIC_ACCESS_SHA256)

    def test_hash_source_member_or_binding_drift_refused(self):
        for drift in ("hash", "source", "member", "run", "image", "probe", "lock"):
            with self.subTest(drift=drift):
                args = self.fixture()
                if drift == "hash":
                    args[4]["source_sha256"]["src/hestiarelay/access.py"] = "0" * 64
                elif drift == "source":
                    args[3] += b"\n"
                elif drift == "member":
                    args[2] = args[2].replace(b'access.py":"', b'otherx.py":"', 1)
                elif drift == "run":
                    args[4]["run_id"] = "999"
                elif drift == "image":
                    args[5]["image_id"] = "sha256:" + "0" * 64
                else:
                    native = json.loads(args[2])
                    if drift == "probe":
                        native["binding"]["probe_sha256"] = "0" * 64
                    else:
                        native["image_runtime_lock_sha256"] = "0" * 64
                    args[2] = json.dumps(native, sort_keys=True, separators=(",", ":")).encode()
                self.assertTrue(self.classify(args)["blocking"])

    def test_new_finding_alongside_reviewed_is_blocking(self):
        args = self.fixture()
        newer = dict(inventory.REVIEWED_ARTIFACT_FINDING, Fingerprint="new:jwt:1", RuleID="jwt")
        args[0] = json.dumps([inventory.REVIEWED_ARTIFACT_FINDING, newer]).encode()
        result = self.classify(args)
        self.assertTrue(result["blocking"])
        self.assertEqual(result["accepted_count"], 0)

    def test_error_malformed_or_column_bounds_block(self):
        for drift in ("exit2", "exit_minus1", "bool", "object", "invalid_json",
                      "duplicate_member", "columns", "clean_with_finding"):
            with self.subTest(drift=drift):
                args = self.fixture()
                if drift in ("exit2", "exit_minus1", "bool", "clean_with_finding"):
                    args[1] = {"exit2": 2, "exit_minus1": -1, "bool": True,
                               "clean_with_finding": 0}[drift]
                elif drift == "object":
                    args[0] = b"{}"
                elif drift == "invalid_json":
                    args[0] = b"["
                elif drift == "duplicate_member":
                    args[0] = b'[{"RuleID":"generic-api-key","RuleID":"jwt"}]'
                else:
                    wrong = dict(inventory.REVIEWED_ARTIFACT_FINDING, EndColumn=9999999)
                    args[0] = json.dumps([wrong]).encode()
                result = self.classify(args)
                self.assertTrue(result["blocking"])
                self.assertEqual(result["accepted_count"], 0)



class NpmBindingIntegrationTests(unittest.TestCase):
    """Real file capture/verify; run identities and advisory reports are synthetic."""
    qualified_install = None
    receipts = []

    @contextlib.contextmanager
    def fixture(self):
        source_inputs = {
            name: (SCRIPTS.parent / name).read_bytes()
            for name in ("tools/inspector/package.json", "tools/inspector/package-lock.json")
        }
        if self.qualified_install is None:
            # Portable source-guard fixture, never an actual Inspector installation claim.
            package = {"name": "@modelcontextprotocol/inspector", "version": "2.9.0",
                       "bin": {"mcp-inspector": "cli/build/index.js"}}
            manifest = json.dumps(package).encode()
            entry = b"// SYNTHETIC source-guard fixture; never invoked\n"
            identity = {**inventory.INSPECTOR_IDENTITY,
                        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
                        "entry_sha256": hashlib.sha256(entry).hexdigest()}
            mode = "SYNTHETIC_SOURCE_GUARD"
        else:
            root = Path(self.qualified_install) / "node_modules/@modelcontextprotocol/inspector"
            manifest = (root / "package.json").read_bytes()
            package = json.loads(manifest)
            entry = (root / package["bin"]["mcp-inspector"]).read_bytes()
            identity = {**inventory.INSPECTOR_IDENTITY,
                        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
                        "entry_sha256": hashlib.sha256(entry).hexdigest()}
            self.assertEqual(identity, inventory.INSPECTOR_IDENTITY)
            mode = "QUALIFIED_INSTALL_BYTES_WITH_SYNTHETIC_RUN_AND_AUDIT"
        previous = Path.cwd()
        with tempfile.TemporaryDirectory(prefix="hestia-npm-binding-") as temporary:
            try:
                os.chdir(temporary)
                for name, data in source_inputs.items():
                    target = Path(name)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                Path("qa-artifacts/release").mkdir(parents=True)
                Path("qa-artifacts/inspector-package-lock.json").write_bytes(
                    source_inputs["tools/inspector/package-lock.json"]
                )
                root = Path("tools/inspector/node_modules/@modelcontextprotocol/inspector")
                root.mkdir(parents=True)
                (root / "package.json").write_bytes(manifest)
                cli = root / package["bin"]["mcp-inspector"]
                cli.parent.mkdir(parents=True, exist_ok=True)
                cli.write_bytes(entry)
                link = Path("tools/inspector/node_modules/.bin/mcp-inspector")
                link.parent.mkdir(parents=True)
                link.symlink_to(cli.resolve())
                attempt = {"source_commit": "SYNTHETIC-REVIEW07-COMMIT",
                           "run_id": "SYNTHETIC-REVIEW07-RUN", "run_attempt": "1"}
                container = {"mcp_inspector": identity.copy(), "scope": "SYNTHETIC_RECEIPT"}
                audit = {"auditReportVersion": 2, "vulnerabilities": {}, "metadata": {
                    "vulnerabilities":
                        {k: 0 for k in ("info", "low", "moderate", "high", "critical", "total")}}}

                def source_command(*args):
                    self.assertEqual(args, ("git", "rev-parse", "HEAD"))
                    return attempt["source_commit"]

                with (
                    patch.object(inventory, "command", side_effect=source_command),
                    patch.object(inventory, "INSPECTOR_IDENTITY", identity),
                    patch.dict(os.environ, {"GITHUB_RUN_ID": attempt["run_id"],
                                             "GITHUB_RUN_ATTEMPT": "1"}),
                ):
                    yield attempt, container, audit, cli, mode
            finally:
                os.chdir(previous)

    def capture(self):
        inventory.capture_npm_binding()
        raw = Path("qa-artifacts/release/npm-audit-binding.json").read_bytes()
        report = inventory.unique_json(raw)
        self.assertEqual(report["status"], "PASS")
        return report

    def record(self, scenario, mode, variants):
        self.receipts.append({"scenario": scenario, "status": "PASS", "mode": mode,
                              "variants": variants, "npm_audit_live": False,
                              "mcp_CLI_invoked": False, "new_install_in_fixture": False})

    def test_positive_capture_write_readback_verify(self):
        with self.fixture() as (attempt, container, audit, _cli, mode):
            report = self.capture()
            inventory.verify_npm_binding(report, attempt, container, audit, 0)
            self.assertEqual(report["source_commit"], attempt["source_commit"])
            self.assertEqual(report["input_sha256"], inventory.NPM_INPUT_SHA256)
            self.record("1_CAPTURE_WRITE_READBACK_VERIFY", mode, 1)

    def test_postcapture_package_lock_and_entry_drift_refused(self):
        for name in ("package", "lock", "entry"):
            with self.subTest(drift=name), self.fixture() as (attempt, container, audit, cli, mode):
                report = self.capture()
                target = {"package": Path("tools/inspector/package.json"),
                          "lock": Path("tools/inspector/package-lock.json"), "entry": cli}[name]
                target.write_bytes(target.read_bytes() + b"\n")
                with self.assertRaises(AssertionError):
                    inventory.verify_npm_binding(report, attempt, container, audit, 0)
        self.record("2_POSTCAPTURE_DRIFT_REFUSED", mode, 3)

    def test_capture_error_enolock_errorjson_and_metadata_refused(self):
        with self.fixture() as (attempt, container, audit, _cli, mode):
            Path("qa-artifacts/inspector-package-lock.json").unlink()
            with self.assertRaisesRegex(AssertionError, "input binding failed"):
                inventory.capture_npm_binding()
            report = json.loads(Path("qa-artifacts/release/npm-audit-binding.json").read_bytes())
            self.assertEqual(report["status"], "BLOCK")
            with self.assertRaises(AssertionError):
                inventory.verify_npm_binding(report, attempt, container, audit, 2)
        for issue in ("capture_exit", "ENOLOCK", "other_error", "metadata"):
            with (
                self.subTest(issue=issue),
                self.fixture() as (attempt, container, audit, _cli, mode),
            ):
                report = self.capture()
                status = 2 if issue == "capture_exit" else 0
                if issue in ("ENOLOCK", "other_error"):
                    audit["error"] = {"code": issue, "scope": "SYNTHETIC"}
                elif issue == "metadata":
                    del audit["metadata"]["vulnerabilities"]["critical"]
                with self.assertRaises((AssertionError, KeyError)):
                    inventory.verify_npm_binding(report, attempt, container, audit, status)
        self.record("3_ERRORS_REFUSED_WITHOUT_PASS", mode, 5)



if __name__ == "__main__":
    unittest.main(verbosity=2)
