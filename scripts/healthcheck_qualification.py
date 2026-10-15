"""Private SOURCE_ONLY candidate; never run in unit12.

One admitted job builds one image and starts one unprivileged container. This
is only healthcheck qualification, never a release/security acceptance gate.
All subprocess originals and receipts precede parsing/checks; final process
exit must be checked by the external owner before POST_RETURN is claimed.
"""

import argparse
import hashlib
import io
import json
import os
import selectors
import shutil
import subprocess
import tarfile
import time
from pathlib import Path, PurePosixPath

BASE = "d3f15f3fa4347dc781e43479282c6372d80ddbc0"
BEFORE = "70cf3bf917b41948071ba0e2627a0c5b0e3dfa2640929ca504cb60b46f36f8e8"
AFTER = "a648a4fce31814b78ce01afde3691d96ff9cad755893321aa42404abbe8273bb"
CODE = "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
EXPECTED_HEALTH = ["CMD", "python", "-c", CODE]
EXPECTED_CMD = [
    "python",
    "-m",
    "uvicorn",
    "hestiarelay.server:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000",
    "--no-proxy-headers",
]
MAX_ORIGINAL_BYTES = 16 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


class CommandNotAccepted(RuntimeError):
    def __init__(self, receipt):
        self.receipt = receipt
        super().__init__(receipt["label"] + ":" + receipt["verdict"])


class NativeCommandOps:
    "Real operations are used only by a separately admitted future runtime."

    now = staticmethod(time.monotonic)
    pause = staticmethod(time.sleep)

    def spawn(self, argv, cwd, env):
        return subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )

    def streams(self, proc):
        return [(proc.stdout, 0, True), (proc.stderr, 1, True)]

    def mux(self):
        return selectors.DefaultSelector()

    def register(self, mux, stream, index):
        os.set_blocking(stream.fileno(), False)
        mux.register(stream, selectors.EVENT_READ, index)

    def events(self, mux, delay):
        return [(key.fileobj, key.data) for key, _ in mux.select(delay)]

    def read(self, stream):
        try:
            return os.read(stream.fileno(), 65536)
        except BlockingIOError:
            return None

    def poll(self, proc):
        return proc.poll()  # WNOHANG, never wait(timeout) after EOF.

    def signal(self, proc):
        os.killpg(proc.pid, 9)  # At most one attempt; no backend-stop claim.

    def unregister(self, mux, stream):
        mux.unregister(stream)

    def close_stream(self, stream):
        stream.close()  # Close owned stream object once, never os.close + close.

    def close_mux(self, mux):
        mux.close()


def finalize_command_retention(
    label,
    argv,
    output,
    state,
    ops,
    persist,
    buffers,
    observed,
    rc,
    operation_errors,
    stamps,
    deadline,
    work_deadline,
    drain_deadline,
    reserve,
    raw_complete,
    reasons,
    signal_attempts,
    owned_closed,
    cleanup=False,
):
    "Originals/primary live in RAM before fallible I/O. RAM is not crash custody."
    retention_errors = []

    def note(reason):
        if reason not in reasons:
            reasons.append(reason)

    def latch():
        if state.get("first_unknown") is None:
            state["first_unknown"] = {"label": label, "reasons": reasons.copy(), "returncode": rc}

    def fault(operation, error):
        retention_errors.append(
            {"operation": operation, "type": type(error).__name__, "message": str(error)}
        )
        note("RETENTION_OR_CLOCK_UNKNOWN")
        latch()

    def clock(phase):
        try:
            value = ops.now()
            if not isinstance(value, (float, int)) or not __import__("math").isfinite(value):
                raise ValueError("nonfinite monotonic observation")
            stamps[phase] = value
            if value >= deadline:
                note("RETENTION_RETURN_AFTER_ABSOLUTE_DEADLINE")
                latch()
            return value
        except Exception as error:
            stamps[phase] = None
            fault(phase, error)
            return None

    original = {
        "label": label,
        "argv": argv,
        "returncode": rc,
        "operation_errors": operation_errors.copy(),
        "original_bytes_observed": observed.copy(),
        "retained_bytes": [len(x) for x in buffers],
        "sha256": [sha(x) for x in buffers],
        "phase_timestamps": stamps.copy(),
    }
    # First retain immutable originals and primary in memory, before fs/open/clock.
    state.setdefault("originals_ram", {})[label] = {
        "stdout": bytes(buffers[0]),
        "stderr": bytes(buffers[1]),
        "metadata": original.copy(),
        "retention_errors": retention_errors,
    }
    if not raw_complete:
        note("RAW_OR_TERMINAL_INCOMPLETE")
    if rc != 0:
        note("NONZERO_OR_UNOBSERVED_ORIGINAL_RETURNCODE")
    if reasons:
        latch()
    for suffix, data in zip(["stdout", "stderr"], buffers, strict=False):
        try:
            with (output / (label + "." + suffix)).open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception as error:
            fault("original_" + suffix, error)
    try:
        write(output / (label + ".original.json"), original)
    except Exception as error:
        fault("original_metadata", error)
    clock("POST_RETENTION")
    preliminary = dict(
        original,
        phase_timestamps=stamps.copy(),
        absolute_deadline=deadline,
        functional_deadline=work_deadline,
        drain_deadline=drain_deadline,
        drain_reserved_seconds=reserve,
        raw_complete=raw_complete,
        complete=raw_complete and rc == 0 and not reasons,
        verdict="UNKNOWN_NOT_ACCEPTED",
        reasons=reasons.copy(),
        signal_attempts=signal_attempts,
        terminal_observed=rc is not None,
        backend_stop="NOT_CLAIMED",
        owned_streams_closed_once=owned_closed,
        cleanup=cleanup,
        retention_errors=retention_errors.copy(),
        final_verdict=False,
    )
    if preliminary["complete"]:
        preliminary["verdict"] = "TIMELY_EXIT0_PRELIMINARY"
    receipt_path = output / (label + ".receipt.json")
    # Exactly one persistence call. A partial or complete original is never retried.
    try:
        persist(receipt_path, preliminary)
    except Exception as error:
        fault("receipt_persist", error)
    clock("POST_RECEIPT_PERSIST")
    accepted = raw_complete and rc == 0 and not reasons
    final = dict(
        preliminary,
        phase_timestamps=stamps.copy(),
        complete=accepted,
        verdict="TIMELY_EXIT0_ACCEPTED" if accepted else "UNKNOWN_NOT_ACCEPTED",
        reasons=reasons.copy(),
        final_verdict=True,
        retention_errors=retention_errors,
        original_receipt=receipt_path.name,
    )
    state.setdefault("calls", []).append(final)
    if not accepted:
        latch()
        if cleanup:
            state.setdefault("cleanup_errors", []).append(final)
        # Distinct diagnostic, one best-effort attempt, no retry or new authority.
        try:
            write(
                output / (label + ".closeout.json"),
                dict(
                    final,
                    administrative_only=True,
                    new_functional_authority=False,
                    original_not_rewritten=True,
                ),
            )
        except Exception as error:
            fault("administrative_closeout", error)
        raise CommandNotAccepted(final)
    return bytes(buffers[0])


def bounded_command(
    label,
    argv,
    timeout,
    output,
    state,
    *,
    ops=None,
    cwd=None,
    env=None,
    cleanup=False,
    persist=None,
):
    """Absolute request/invoke/return deadlines with a reserved finite drain.

    Dependency injection is used by the one inert group. It does not qualify
    native scheduling, kernel I/O, process-group termination or Docker daemon.
    """
    ops = NativeCommandOps() if ops is None else ops
    persist = write if persist is None else persist
    try:
        pre_request = ops.now()
        if not isinstance(pre_request, (float, int)) or not __import__("math").isfinite(
            pre_request
        ):
            raise ValueError("nonfinite PRE_REQUEST clock")
    except Exception as error:
        r = {
            "label": label,
            "argv": argv,
            "returncode": None,
            "complete": False,
            "raw_complete": False,
            "final_verdict": True,
            "verdict": "UNKNOWN_NOT_ACCEPTED",
            "reasons": ["PRE_REQUEST_CLOCK_UNKNOWN"],
            "retention_errors": [{"operation": "PRE_REQUEST", "type": type(error).__name__}],
            "backend_stop": "NOT_CLAIMED",
        }
        state.setdefault("originals_ram", {})[label] = {
            "stdout": b"",
            "stderr": b"",
            "metadata": r.copy(),
        }
        if state.get("first_unknown") is None:
            state["first_unknown"] = {
                "label": label,
                "reasons": r["reasons"].copy(),
                "returncode": None,
            }
        state.setdefault("calls", []).append(r)
        raise CommandNotAccepted(r) from error
    deadline = pre_request + max(0, timeout)
    reserve = min(0.25, max(0, timeout) / 10)
    work_deadline = deadline - reserve
    stamps = {"PRE_REQUEST": pre_request}
    buffers, observed = [bytearray(), bytearray()], [0, 0]
    reasons, operation_errors = [], []
    proc, mux, streams, rc = None, None, [], None
    closed, eof = set(), set()
    signal_attempts, polls = 0, 0
    drain_deadline = None
    cleanup_key = tuple(argv)
    blocked = state.get("first_unknown") is not None and not cleanup
    duplicate_cleanup = cleanup and cleanup_key in state.setdefault("cleanup_issued", [])
    if cleanup and not duplicate_cleanup:
        state["cleanup_issued"].append(cleanup_key)

    def note(reason):
        if reason not in reasons:
            reasons.append(reason)

    def close_one(stream, owned):
        key = id(stream)
        if key in closed:
            return
        closed.add(key)  # Claim once even if a close/unregister operation fails.
        if mux is not None:
            try:
                ops.unregister(mux, stream)
            except Exception as error:
                operation_errors.append("unregister:" + type(error).__name__)
                note("FD_UNREGISTER_UNKNOWN")
        if owned:
            try:
                ops.close_stream(stream)
            except Exception as error:
                operation_errors.append("close:" + type(error).__name__)
                note("FD_CLOSE_UNKNOWN")

    try:
        if blocked or duplicate_cleanup:
            note("FUNCTIONAL_BARRIER_AFTER_FIRST_UNKNOWN" if blocked else "CLEANUP_REPLAY_REFUSED")
        elif timeout <= 0:
            note("DEADLINE_BEFORE_REQUEST")
        else:
            stamps["PRE_INVOKE"] = ops.now()
            if stamps["PRE_INVOKE"] >= work_deadline:
                note("DEADLINE_BEFORE_INVOKE")
            else:
                proc = ops.spawn(argv, cwd, env)
                stamps["POST_INVOKE"] = ops.now()
                streams = ops.streams(proc)
                mux = ops.mux()
                for stream, index, _ in streams:
                    ops.register(mux, stream, index)
                while True:
                    polls += 1
                    if polls > 20000:
                        note("FINITE_POLL_COUNT_EXHAUSTED")
                    rc = ops.poll(proc)
                    now = ops.now()
                    if now >= deadline:
                        note("POST_RETURN_LATE_OR_TERMINAL_UNOBSERVED")
                    if len(eof) == len(streams) and rc is not None:
                        stamps["POST_RETURN"] = now
                        if now >= work_deadline:
                            note("FUNCTIONAL_RETURN_AFTER_RESERVED_DEADLINE")
                        break
                    if now >= work_deadline:
                        note("FUNCTIONAL_DEADLINE_EXHAUSTED")
                    if reasons and drain_deadline is None:
                        drain_deadline = min(deadline, now + reserve)
                        if rc is None and signal_attempts == 0:
                            signal_attempts = 1
                            try:
                                ops.signal(proc)
                            except Exception as error:
                                operation_errors.append("signal:" + type(error).__name__)
                                note("SIGNAL_RESULT_UNKNOWN")
                    stop = deadline if drain_deadline is None else drain_deadline
                    now = ops.now()
                    if now >= stop or polls > 20000:
                        break
                    ready = (
                        ops.events(mux, min(0.05, stop - now)) if len(eof) < len(streams) else []
                    )
                    if not ready and len(eof) == len(streams):
                        ops.pause(min(0.01, max(0, stop - ops.now())))
                    for stream, index in ready:
                        if ops.now() >= stop:
                            note("READ_BOUNDARY_REACHED")
                            break
                        data = ops.read(stream)
                        if data is None:
                            continue
                        if not data:
                            eof.add(id(stream))
                            owned = next(owned for value, _, owned in streams if value is stream)
                            close_one(stream, owned)
                            continue
                        observed[index] += len(data)
                        available = max(0, MAX_ORIGINAL_BYTES - state.get("retained_bytes", 0))
                        keep = data[:available]
                        buffers[index].extend(keep)
                        state["retained_bytes"] = state.get("retained_bytes", 0) + len(keep)
                        if len(keep) < len(data):
                            note("OUTPUT_OVERFLOW_INCOMPLETE")
                if rc is None:
                    rc = ops.poll(proc)  # One nonblocking terminal observation; never wait.
                stamps["POST_RETURN"] = ops.now()
                if stamps["POST_RETURN"] >= deadline:
                    note("POST_RETURN_LATE_OR_TERMINAL_UNOBSERVED")
                if rc is None:
                    note("TERMINAL_NOT_OBSERVED_NO_BACKEND_STOP_CLAIM")
                elif rc != 0:
                    note("NONZERO_ORIGINAL_RETURNCODE")
    except Exception as error:
        operation_errors.append(type(error).__name__ + ": " + str(error))
        note("COMMAND_OPERATION_UNKNOWN")
    finally:
        for stream, _, owned in streams:
            close_one(stream, owned)
        if mux is not None:
            try:
                ops.close_mux(mux)
            except Exception as error:
                operation_errors.append("mux_close:" + type(error).__name__)
                note("MUX_CLOSE_UNKNOWN")
        if "POST_RETURN" not in stamps:
            try:
                stamps["POST_RETURN"] = ops.now()
            except Exception as error:
                operation_errors.append("POST_RETURN_CLOCK:" + type(error).__name__)
                note("POST_RETURN_CLOCK_UNKNOWN")
        raw_complete = (
            proc is not None
            and len(eof) == len(streams)
            and rc is not None
            and observed == [len(x) for x in buffers]
        )
        retained = finalize_command_retention(
            label,
            argv,
            output,
            state,
            ops,
            persist,
            buffers,
            observed,
            rc,
            operation_errors,
            stamps,
            deadline,
            work_deadline,
            drain_deadline,
            reserve,
            raw_complete,
            reasons,
            signal_attempts,
            sum(owned and id(stream) in closed for stream, _, owned in streams),
            cleanup,
        )
    return retained


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--admission", type=Path, required=True)
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    args = ap.parse_args()
    out = args.output.resolve()
    out.mkdir(mode=0o700, parents=False, exist_ok=False)
    result = {
        "schema": "HESTIA_HEALTHCHECK_QUALIFICATION_RESULT_V1",
        "status": "BLOCKED",
        "POST_RETURN": "REQUIRES_EXTERNAL_PROCESS_EXIT_AND_ARTIFACT_READBACK",
        "calls": [],
        "build_attempts": 0,
        "container_start_attempts": 0,
        "cleanup_attempts": 0,
        "security_release": "BLOCKED",
        "native_libraries_row_bindings": "NEW_IMAGE_UNMEASURED; OLD_POSIX_PROOF_NOT_INHERITED",
    }
    used = 0
    container_name = None
    image_id = None
    admitted = False
    run_attempted = False
    cleanup_ok = True
    boundary = None
    env = None
    docker = None

    command_state = {
        "calls": result["calls"],
        "retained_bytes": 0,
        "first_unknown": None,
        "cleanup_issued": [],
    }

    def command(label, argv, timeout, cwd=None, cleanup=False):
        nonlocal used
        try:
            return bounded_command(
                label, argv, timeout, out, command_state, cwd=cwd, env=env, cleanup=cleanup
            )
        finally:
            used = command_state["retained_bytes"]

    try:
        admission_raw = args.admission.read_bytes()
        contract_raw = args.contract.read_bytes()
        (out / "admission.original.json").write_bytes(admission_raw)
        (out / "contract.original.json").write_bytes(contract_raw)
        admission = json.loads(admission_raw)
        contract = json.loads(contract_raw)
        required = [
            "isolated_route",
            "provider_cost_quota",
            "build_host_resources",
            "network_dependency_sources",
            "exact_run_identity",
            "separate_runtime_authority",
        ]
        if admission.get("runtime_admitted") is not True or admission.get("contract_sha256") != sha(
            contract_raw
        ):
            raise ValueError("runtime_admission_or_exact_contract_missing")
        for key in required:
            proof = admission.get("proofs", {}).get(key, {})
            if (
                proof.get("state") != "PROVED"
                or not proof.get("evidence_ref")
                or len(proof.get("evidence_sha256", "")) != 64
            ):
                raise ValueError("unproven_required_gate:" + key)
        native_run_id = os.environ.get("GITHUB_RUN_ID", "")
        if os.environ.get("GITHUB_RUN_ATTEMPT") != "1" or not native_run_id.isdecimal():
            raise ValueError("actual_native_first_attempt_run_required")
        if admission.get("expected_run_id") not in (None, native_run_id):
            raise ValueError("exact_provider_run_mismatch")
        if (
            admission.get("run_binding_mode") != "BIND_NATIVE_RUN_ON_SINGLE_ADMITTED_DISPATCH"
            or admission.get("dispatch_invocations") != 1
            or admission.get("dispatch_retry") != 0
        ):
            raise ValueError("external_single_dispatch_ledger_required")
        if (
            sha(Path(__file__).read_bytes())
            != contract["candidate_files"]["scripts/healthcheck_qualification.py"]["sha256"]
        ):
            raise ValueError("script_identity_mismatch")
        write(
            out / "INTENT.json",
            {
                "effect_key": admission["effect_key"],
                "run_id": native_run_id,
                "run_attempt": 1,
                "external_dispatch_ledger": admission["proofs"]["exact_run_identity"],
                "build": 1,
                "container_start": 1,
                "retry": 0,
                "provider_exactly_once": (
                    "NOT_CLAIMED; external owner must issue one journ"
                    "aled dispatch and reconcile unknown without retr"
                    "y"
                ),
            },
        )
        admitted = True
        # Empty Docker config and sanitized CLI env: no credential/remote-daemon forwarding.
        cfg = out / "empty-docker-config"
        cfg.mkdir(mode=0o700)
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(cfg),
            "DOCKER_CONFIG": str(cfg),
            "DOCKER_BUILDKIT": "1",
            "BUILDKIT_PROGRESS": "plain",
            "LC_ALL": "C",
        }
        git, docker = shutil.which("git"), shutil.which("docker")
        if not git or not docker:
            raise ValueError("preinstalled_git_or_docker_missing_no_install")
        preflight_deadline = time.monotonic() + 30
        head = command("source-head", [git, "rev-parse", "HEAD"], 5, args.source).decode().strip()
        if head != BASE or contract["baseline"]["current_PR_head"] != BASE:
            raise ValueError("source_head_drift_no_rebase")
        original = command(
            "source-archive",
            [
                git,
                "archive",
                "--format=tar",
                BASE,
                "Dockerfile",
                "requirements-runtime.txt",
                "LICENSE",
                "src",
                ".dockerignore",
            ],
            10,
            args.source,
        )
        if len(original) > 8 * 1024 * 1024:
            raise ValueError("buildcontext_archive_bound")
        context = out / "context"
        context.mkdir(mode=0o700)
        with tarfile.open(fileobj=io.BytesIO(original), mode="r:") as archive:
            members = archive.getmembers()
            if len(members) > 256:
                raise ValueError("buildcontext_member_bound")
            seen = set()
            for item in members:
                path = PurePosixPath(item.name)
                if (
                    item.name in seen
                    or path.is_absolute()
                    or ".." in path.parts
                    or "\\" in item.name
                    or not (item.isdir() or item.isreg())
                    or item.size > 4 * 1024 * 1024
                ):
                    raise ValueError("unsafe_buildcontext_entry")
                seen.add(item.name)
            for item in members:
                dest = context / item.name
                if item.isdir():
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with dest.open("xb") as handle:
                        shutil.copyfileobj(archive.extractfile(item), handle)
        dockerfile = context / "Dockerfile"
        before = dockerfile.read_bytes()
        if sha(before) != BEFORE:
            raise ValueError("Dockerfile_preimage_drift")
        old = '    CMD python -c "' + CODE + '"'
        new = "    CMD " + json.dumps(["python", "-c", CODE])
        text = before.decode()
        if text.count(old) != 1:
            raise ValueError("healthcheck_unique_preimage_missing")
        after = text.replace(old, new).encode()
        if sha(after) != AFTER:
            raise ValueError("Dockerfile_postimage_mismatch")
        dockerfile.write_bytes(after)
        hashes = {
            f.relative_to(context).as_posix(): sha(f.read_bytes())
            for f in sorted(context.rglob("*"))
            if f.is_file()
        }
        write(
            out / "build-context-manifest.json",
            {
                "base_source_commit": BASE,
                "transient_Dockerfile_override_sha256": AFTER,
                "files": hashes,
                "pending07": "UNAPPLIED_RETAINED_DISJOINT_NON_BUILD_CONTEXT_PATHS",
            },
        )
        if time.monotonic() > preflight_deadline:
            raise TimeoutError("source_preflight30s")
        run_key = native_run_id
        if not run_key.isdecimal():
            raise ValueError("invalid_exact_run_id")
        container_name = "hestia-healthcheck-" + run_key
        tag = "hestiarelay:healthcheck-" + run_key
        build_start = time.monotonic()
        boundary = build_start + 990  # Build<=900, then health+cleanup<=90.
        result["build_attempts"] = 1
        command(
            "build",
            [
                docker,
                "build",
                "--pull",
                "--no-cache",
                "--iidfile",
                str(out / "new-image.id"),
                "--tag",
                tag,
                str(context),
            ],
            900,
        )
        boundary = min(boundary, time.monotonic() + 90)
        image_id = (out / "new-image.id").read_text().strip()
        if not image_id.startswith("sha256:") or len(image_id) != 71:
            raise ValueError("new_image_id_missing")
        result["new_image_id"] = image_id
        inspect_format = (
            '{"Id":{{json .Id}},"Healthcheck":{{json .Config.'
            'Healthcheck.Test}},"Cmd":{{json .Config.Cmd}},"U'
            'ser":{{json .Config.User}},"Layers":{{json .Root'
            "FS.Layers}}}"
        )
        meta_raw = command(
            "image-inspect",
            [docker, "image", "inspect", "--format", inspect_format, image_id],
            min(5, boundary - time.monotonic() - 15),
        )
        meta = json.loads(meta_raw)
        if (
            meta["Id"] != image_id
            or meta["Healthcheck"] != EXPECTED_HEALTH
            or meta["Cmd"] != EXPECTED_CMD
            or meta["User"] != "10001:10001"
        ):
            raise ValueError("image_healthcheck_CMD_User_or_digest_mismatch")
        result["image_configuration"] = meta
        result["container_start_attempts"] = 1
        run_attempted = True
        command(
            "run",
            [
                docker,
                "run",
                "--detach",
                "--name",
                container_name,
                "--network",
                "none",
                "--read-only",
                "--user",
                "10001:10001",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--memory",
                "512m",
                "--pids-limit",
                "128",
                "--cpus",
                "1",
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777",
                "--tmpfs",
                "/data:rw,noexec,nosuid,nodev,size=16m,uid=10001,gid=10001,mode=0700",
                image_id,
            ],
            min(10, boundary - time.monotonic() - 15),
        )
        resource_format = (
            '{"State":{{json .State.Status}},"Health":{{json '
            '.State.Health.Status}},"Image":{{json .Image}},"'
            'User":{{json .Config.User}},"Host":{{json .HostC'
            'onfig}},"Mounts":{{json .Mounts}}}'
        )
        healthy = False
        for index in range(15):
            remaining = boundary - time.monotonic() - 15
            if remaining <= 0:
                raise TimeoutError("health_deadline_cleanup_reserved")
            state = json.loads(
                command(
                    "health-" + str(index),
                    [docker, "inspect", "--format", resource_format, container_name],
                    min(3, remaining),
                )
            )
            host = state["Host"]
            if (
                state["Image"] != image_id
                or state["User"] != "10001:10001"
                or host["Privileged"]
                or not host["ReadonlyRootfs"]
                or host["NetworkMode"] != "none"
                or host["Memory"] != 536870912
                or host["PidsLimit"] != 128
                or host["NanoCpus"] != 1000000000
                or "ALL" not in host["CapDrop"]
                or not any(x.startswith("no-new-privileges") for x in host["SecurityOpt"])
                or host.get("Binds")
                or any(x["Type"] != "tmpfs" for x in state["Mounts"])
            ):
                raise ValueError("effective_container_resource_or_privilege_guard_failed")
            if state["State"] != "running" or state["Health"] == "unhealthy":
                raise ValueError("container_not_running_or_unhealthy")
            if state["Health"] == "healthy":
                healthy = True
                result["effective_runtime_guards"] = state
                break
            time.sleep(min(4, max(0, boundary - time.monotonic() - 15)))
        if not healthy:
            raise TimeoutError("healthy_not_observed_in_finite_window")
        result["status"] = "QUALIFICATION_OBSERVED_PENDING_CLEANUP_AND_POST_RETURN"
    except Exception as error:
        result["status"] = "UNKNOWN" if admitted else "BLOCKED"
        result["first_error"] = type(error).__name__ + ": " + str(error)
    finally:
        # Single attempt per owned resource; never restart/build again to repair.
        if result["build_attempts"] and image_id is None:
            result["partial_build_cleanup"] = (
                "UNKNOWN; no completed owned image identity, no blind global prune/remove"
            )
        if admitted and docker is not None and (run_attempted or image_id):
            result["cleanup_attempts"] = 1
            cleanup_deadline = (
                min(time.monotonic() + 15, boundary) if boundary else time.monotonic() + 15
            )
            if run_attempted:
                try:
                    command(
                        "cleanup-container",
                        [docker, "rm", "--force", "--volumes", container_name],
                        min(8, cleanup_deadline - time.monotonic()),
                        cleanup=True,
                    )
                except Exception as error:
                    cleanup_ok = False
                    result["container_cleanup_error"] = str(error)
            if image_id:
                try:
                    command(
                        "cleanup-image",
                        [docker, "image", "rm", image_id],
                        cleanup_deadline - time.monotonic(),
                        cleanup=True,
                    )
                except Exception as error:
                    cleanup_ok = False
                    result["image_cleanup_error"] = str(error)
            if not cleanup_ok or boundary is not None and time.monotonic() > boundary:
                result["status"] = "UNKNOWN"
                result["cleanup_or_late_return"] = "UNKNOWN_OR_DEADLINE_EXCEEDED"
        if (
            result["status"] == "QUALIFICATION_OBSERVED_PENDING_CLEANUP_AND_POST_RETURN"
            and cleanup_ok
        ):
            result["status"] = (
                "TARGET_HEALTHCHECK_OBSERVED_CLEANUP_COMPLETE_EXTERNAL_POST_RETURN_REQUIRED"
            )
        result["first_command_unknown"] = command_state["first_unknown"]
        result["cleanup_command_errors"] = [
            r["label"] for r in command_state.get("cleanup_errors", [])
        ]
        result["raw_bytes_retained"] = used
        result["retry_count"] = 0
        write(out / "result.json", result)
        print(
            json.dumps(
                {k: v for k, v in result.items() if k not in {"calls", "effective_runtime_guards"}},
                sort_keys=True,
            )
        )
    return (
        0
        if result["status"]
        == ("TARGET_HEALTHCHECK_OBSERVED_CLEANUP_COMPLETE_EXTERNAL_POST_RETURN_REQUIRED")
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
