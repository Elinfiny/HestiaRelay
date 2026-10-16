"""One bounded, read-only native observation; presence never proves reachability."""

import hashlib
import json
import os
import stat
import struct
import time
from pathlib import Path

MAX_FILES = 256
MAX_LOADED = 256
MAX_BYTES = 1024 * 1024
MAX_FILE_BYTES = 64 * 1024 * 1024
PREFIXES = ("/usr/lib/", "/usr/local/lib/", "/usr/local/bin/", "/usr/share/perl", "/usr/bin/")


class ObservationLimit(Exception):
    pass


def elf_metadata(data, check_deadline):
    """Parse bounded ELF section metadata with the image's existing Python stdlib."""
    if data[:4] != b"\x7fELF":
        return {"status": "NOT_ELF"}
    if data[4] not in (1, 2) or data[5] not in (1, 2):
        return {"status": "NOT_OBSERVED", "reason": "unsupported_elf_format"}
    bits = 64 if data[4] == 2 else 32
    endian = "<" if data[5] == 1 else ">"
    header = struct.unpack_from(
        endian + ("HHIQQQIHHHHHH" if bits == 64 else "HHIIIIIHHHHHH"), data, 16
    )
    offset, entry_size, count = header[5], header[10], header[11]
    fmt = endian + ("IIQQQQIIQQ" if bits == 64 else "IIIIIIIIII")
    minimum = struct.calcsize(fmt)
    if not count or count > 2048 or entry_size < minimum:
        return {"status": "NOT_OBSERVED", "reason": "absent_or_extended_section_table"}
    if offset + count * entry_size > len(data):
        return {"status": "NOT_OBSERVED", "reason": "section_table_out_of_bounds"}
    sections = [
        struct.unpack_from(fmt, data, offset + index * entry_size) for index in range(count)
    ]

    def section(index, bound=4 * 1024 * 1024):
        row = sections[index]
        start, length = row[4], row[5]
        if length > bound or start + length > len(data):
            raise ObservationLimit("elf_section_bounds")
        return data[start : start + length]

    def string(table, index):
        if index >= len(table):
            raise ObservationLimit("elf_string_bounds")
        end = table.find(b"\0", index, min(len(table), index + 512))
        if end < 0:
            raise ObservationLimit("elf_string_length")
        return table[index:end].decode("utf-8", errors="replace")

    needed, symbols, build_ids = set(), set(), []
    limited = False
    for index, row in enumerate(sections):
        check_deadline()
        if row[1] not in (7, 6, 11):
            continue
        blob = section(index)
        if row[1] == 7:
            pos = 0
            while pos + 12 <= len(blob):
                check_deadline()
                names, desc, kind = struct.unpack_from(endian + "III", blob, pos)
                name_start = pos + 12
                desc_start = name_start + ((names + 3) & ~3)
                next_pos = desc_start + ((desc + 3) & ~3)
                if next_pos > len(blob):
                    limited = True
                    break
                if (
                    blob[name_start : name_start + names].rstrip(b"\0") == b"GNU"
                    and kind == 3
                    and desc <= 128
                ):
                    build_ids.append(blob[desc_start : desc_start + desc].hex())
                pos = next_pos
            continue
        if row[6] >= count:
            raise ObservationLimit("elf_link_bounds")
        strings = section(row[6])
        record_fmt = (
            endian + ("qQ" if bits == 64 else "iI")
            if row[1] == 6
            else (endian + ("IBBHQQ" if bits == 64 else "IIIBBH"))
        )
        record_size = struct.calcsize(record_fmt)
        stride = row[9] or record_size
        if stride < record_size or len(blob) // stride > 65536:
            raise ObservationLimit("elf_records_limit")
        for pos in range(0, len(blob) - record_size + 1, stride):
            if pos % (64 * stride) == 0:
                check_deadline()
            record = struct.unpack_from(record_fmt, blob, pos)
            if row[1] == 6:
                if record[0] == 0:
                    break
                if record[0] == 1:
                    needed.add(string(strings, record[1]))
            else:
                name = string(strings, record[0])
                if any(
                    value in name
                    for value in (
                        "fnmatch",
                        "posix_memalign",
                        "aligned_alloc",
                        "align_val_t",
                        "pb_ds",
                    )
                ):
                    symbols.add(name)
    if len(needed) > 128 or len(symbols) > 64:
        limited = True
    return {
        "status": "TRUNCATED" if limited else "OBSERVED",
        "bits": bits,
        "byte_order": "little" if endian == "<" else "big",
        "machine": header[1],
        "method": "stdlib_struct_section_metadata_no_load_or_execution",
        "dt_needed": sorted(needed)[:128],
        "relevant_dynamic_symbols": sorted(symbols)[:64],
        "gnu_build_ids": sorted(set(build_ids))[:16],
        "limits": "Dynamic symbols are names only; no call graph, branch or PBDS absence proof",
    }


def observe():
    started = time.monotonic()
    deadline = started + 9.0  # Leave output/exec headroom inside the external ten-second limit.
    report = {
        "schema": "HESTIA_NATIVE_SURFACE_OBSERVATION_V1",
        "status": "OBSERVED",
        "max_elf_files": MAX_FILES,
        "max_loaded_paths": MAX_LOADED,
        "loaded_paths": [],
        "files": [],
        "component_paths": {},
        "missing": [],
        "limits": [],
        "metadata_method": "Existing image Python stdlib; no added tool",
        "reachability": "NOT_DECIDED; maps are one temporal observation",
        "read_scope": "Standard libraries/native extensions/Perl/POD paths only; no data/auth/env",
    }
    files, loaded = {}, set()

    def tick():
        if time.monotonic() >= deadline:
            raise ObservationLimit("time_budget")

    def inspect(path):
        tick()
        resolved = str(Path(path).resolve(strict=True))
        if not resolved.startswith(PREFIXES) or len(resolved) > 512:
            raise ObservationLimit("path_outside_standard_native_scope")
        if resolved in files:
            return resolved
        if len(files) >= MAX_FILES:
            raise ObservationLimit("file_limit")
        row = {"path": resolved, "status": "NOT_OBSERVED"}
        files[resolved] = row
        info = os.stat(resolved, follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE_BYTES:
            raise ObservationLimit("nonregular_or_file_size_limit")
        chunks, digest = [], hashlib.sha256()
        with open(resolved, "rb") as handle:
            while chunk := handle.read(1024 * 1024):
                tick()
                digest.update(chunk)
                chunks.append(chunk)
        data = b"".join(chunks)
        if len(data) != info.st_size:
            raise ObservationLimit("file_changed_during_read")
        row.update(size_bytes=len(data), sha256=digest.hexdigest(), status="OBSERVED")
        try:
            row["elf"] = elf_metadata(data, tick)
        except ObservationLimit:
            raise
        except (struct.error, IndexError, ValueError) as error:
            row["elf"] = {"status": "NOT_OBSERVED", "reason": type(error).__name__}
            report["limits"].append("elf_metadata_incomplete:" + resolved)
        tick()
        return resolved

    def sample(path):
        try:
            return inspect(path)
        except OSError as error:
            report["missing"].append(
                {"path": str(path), "status": "NOT_OBSERVED", "reason": type(error).__name__}
            )
            return None

    try:
        # Do not export the raw maps or addresses and never read environ or process memory.
        with open("/proc/1/maps", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                tick()
                if index >= 4096:
                    raise ObservationLimit("maps_line_limit")
                parts = line.rstrip().split(maxsplit=5)
                if len(parts) != 6 or not parts[5].startswith(
                    ("/usr/lib/", "/usr/local/lib/", "/lib/", "/usr/local/bin/")
                ):
                    continue
                path = parts[5]
                if path.endswith(" (deleted)"):
                    report["limits"].append("deleted_mapped_library_not_hashed")
                    continue
                if path in loaded:
                    continue
                if len(loaded) >= MAX_LOADED:
                    raise ObservationLimit("loaded_path_limit")
                loaded.add(path)
                resolved = sample(path)
                report["loaded_paths"].append(
                    {"path": resolved or path, "file_hash_observed": resolved is not None}
                )
        perl_paths = {"/usr/bin/perl", "/usr/bin/perl5.40.1"}
        with os.scandir("/usr/bin") as iterator:
            for index, entry in enumerate(iterator):
                tick()
                if index >= 4096:
                    raise ObservationLimit("perl_entrypoint_directory_limit")
                if entry.name.startswith("perl"):
                    perl_paths.add(entry.path)
        report["perl_entrypoint_prefix_scan"] = "COMPLETE_AT_SAMPLE"
        for name, candidates in {
            "dash": ["/usr/bin/dash"],
            "perl": sorted(perl_paths),
            "libstdc++": [
                "/usr/lib/x86_64-linux-gnu/libstdc++.so.6",
                "/usr/lib/aarch64-linux-gnu/libstdc++.so.6",
            ],
        }.items():
            rows = []
            for path in candidates:
                tick()
                if not Path(path).exists():
                    rows.append({"path": path, "status": "ABSENT_AT_SAMPLE"})
                else:
                    rows.append({"path": path, "file": sample(path)})
            report["component_paths"][name] = rows
        report["image_source_sha256"] = {}
        for index, path in enumerate(Path("/app/src/hestiarelay").glob("*.py")):
            tick()
            if index >= 32 or path.stat().st_size > MAX_BYTES:
                raise ObservationLimit("image_source_file_limit")
            report["image_source_sha256"][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        runtime_lock = Path("/app/requirements-runtime.txt")
        report["image_runtime_lock_sha256"] = hashlib.sha256(runtime_lock.read_bytes()).hexdigest()
        roots = [
            "/usr/share/perl",
            "/usr/share/perl5",
            "/usr/lib/perl",
            "/usr/lib/perl5",
            "/usr/lib/x86_64-linux-gnu/perl",
            "/usr/lib/aarch64-linux-gnu/perl",
            "/usr/local/lib/python3.12/lib-dynload",
            "/usr/local/lib/python3.12/site-packages",
            "/usr/lib/x86_64-linux-gnu",
            "/usr/lib/aarch64-linux-gnu",
        ]
        dirs_seen, entries_seen = 0, 0
        for root in roots:
            tick()
            if not Path(root).is_dir():
                report["missing"].append({"path": root, "status": "ABSENT_AT_SAMPLE"})
                continue
            stack = [Path(root)]
            while stack:
                tick()
                directory = stack.pop()
                dirs_seen += 1
                if dirs_seen > 256:
                    raise ObservationLimit("directory_limit")
                with os.scandir(directory) as iterator:
                    for entry in iterator:
                        tick()
                        entries_seen += 1
                        if entries_seen > 8192:
                            raise ObservationLimit("directory_entry_limit")
                        if entry.is_dir(follow_symlinks=False):
                            if "site-packages" in root or "perl" in root:
                                stack.append(Path(entry.path))
                            continue
                        if ".so" in entry.name or (
                            entry.name == "Text.pm" and directory.name == "Pod"
                        ):
                            sample(entry.path)
    except (ObservationLimit, OSError, struct.error, ValueError) as error:
        report["status"] = "TRUNCATED_UNKNOWN"
        report["limits"].append(
            str(error) if isinstance(error, ObservationLimit) else type(error).__name__
        )
    report["files"] = list(files.values())
    report["elapsed_seconds"] = round(time.monotonic() - started, 6)
    if report["missing"] or report["limits"]:
        report["status"] = "PARTIAL_UNKNOWN" if report["status"] == "OBSERVED" else report["status"]
    payload = json.dumps(report, sort_keys=True, separators=(",", ":"))
    if len(payload.encode()) > MAX_BYTES:
        report.update(
            status="TRUNCATED_UNKNOWN",
            files=[],
            loaded_paths=[],
            component_paths={},
            missing=[],
            limits=["json_byte_limit; detailed observations omitted"],
        )
        payload = json.dumps(report, sort_keys=True, separators=(",", ":"))
    print(payload)


if __name__ == "__main__":
    observe()
