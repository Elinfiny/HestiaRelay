"""Experimental build-only reduction; no claim of vulnerability remediation.

Run solely in the newly owned candidate image's network-disabled build layer.
Any unknown solver output, package drift or incomplete evidence refuses the build.
"""

import hashlib
import json
import os
import re
import stat
import subprocess
import time
from pathlib import Path

TARGETS = ('apt', 'libapt-pkg7.0', 'sqv', 'libstdc++6')
REQUIRED = ('gcc-14-base', 'libgcc-s1', 'libc6', 'libssl3t64', 'openssl',
            'libsqlite3-0', 'ca-certificates', 'perl-base')
QUERY = ('/usr/bin/dpkg-query', '-W', '-f=${Package}\t${binary:Package}\t${Version}\t'
         '${Architecture}\t${db:Status-Abbrev}\t${Essential}\t${Protected}\t'
         '${Depends}\t${Pre-Depends}\n')
SIMULATE = ('/usr/bin/apt-get', '--simulate', '--no-download', 'purge', *TARGETS)
PURGE = ('/usr/bin/apt-get', '--yes', '--no-download', 'purge', *TARGETS)
PACKAGE = r'[a-z0-9][a-z0-9+.-]*(?::[a-z0-9]+)?'
VERSION = r'[0-9A-Za-z.+:~_-]+'
MAX_STREAM = 1048576
MAX_FILES = 40000
MAX_HASH_BYTES = 536870912


class Refusal(ValueError):
    """An unqualified condition, never permission to retry a destructive step."""


def checked_return(out, err, code, deadline, now):
    """Only after original receipt capture; shared by native adapter and inert fixtures."""
    if now > deadline or code != 0 or err:
        raise Refusal('Original native result nonzero/stderr/late UNKNOWN')
    if len(out) > MAX_STREAM or len(err) > MAX_STREAM:
        raise Refusal('Original native result overcap UNKNOWN')
    return out


def inventory(raw):
    rows = {}
    for line in raw.decode('utf-8', errors='strict').splitlines():
        fields = line.split('\t')
        if len(fields) != 9:
            raise Refusal('Unrecognized installed package record')
        base, binary, version, arch, status, essential, protected, depends, pre = fields
        if not re.fullmatch(r'[a-z0-9][a-z0-9+.-]*', base):
            raise Refusal('Invalid logical package base name')
        if arch not in ('amd64', 'all') or not re.fullmatch(VERSION, version):
            raise Refusal('Foreign/unknown architecture or version')
        allowed = (base, base + ':amd64') if arch == 'amd64' else (base,)
        if binary not in allowed or base in rows:
            raise Refusal('Qualifier mismatch, duplicate or logical identity collision')
        if status != 'ii ':
            raise Refusal('Unexpected installed status')
        if essential not in ('', 'no', 'yes') or protected not in ('', 'no', 'yes'):
            raise Refusal('Unknown essential/protected state')
        # Retain every original field and the entire original record, byte-order exact.
        rows[base] = [version, arch, status, essential, protected, depends, pre,
                      base, binary, line]
    if not rows or len(rows) > 512:
        raise Refusal('Package inventory completeness bound')
    return rows


def resolve_identity(token, rows):
    # Bare logical name or EXACT independently observed binary alias only.
    if token in rows:
        return token
    matches = [base for base, fields in rows.items() if token == fields[8]]
    if len(matches) != 1:
        raise Refusal('Unverified foreign/virtual/mismatched package identity')
    return matches[0]


def guard_packages(rows):
    if not set(TARGETS + REQUIRED).issubset(rows):
        raise Refusal('Requested or protected package absent')
    for name in TARGETS:
        if rows[name][3] == 'yes' or rows[name][4] == 'yes':
            raise Refusal('Target is Essential or Protected')
    # Conservative: reject even an alternative referencing a removal target.
    # No speculative virtual-package/alternative dependency resolution.
    for name, fields in rows.items():
        if name in TARGETS:
            continue
        for dependency in fields[5:7]:
            if not dependency:
                continue
            for clause in dependency.split(','):
                for alternative in clause.split('|'):
                    match = re.fullmatch(
                        r'\s*(' + PACKAGE + r')(?:\s*\((?:<<|<=|=|>=|>>)\s*'
                        + VERSION + r'\))?\s*', alternative)
                    if match is None:
                        raise Refusal('Unrepresentable dependency expression')
                    if resolve_identity(match[1], rows) in TARGETS:
                        raise Refusal('Remaining package depends on a target')


def parse_plan(raw, rows):
    lines = raw.decode('utf-8', errors='strict').splitlines()
    prefix = ['Reading package lists...','Building dependency tree...',
              'Reading state information...','The following packages will be REMOVED:']
    if lines[:4] != prefix:
        raise Refusal('Unknown or incomplete solver preamble')
    listed = []
    index = 4
    while index < len(lines) and lines[index].startswith('  '):
        listed.extend(lines[index].split())
        index += 1
    if any(not item.endswith('*') for item in listed):
        raise Refusal('Unexpected removal token')
    logical = [resolve_identity(item[:-1], rows) for item in listed]
    if len(logical) != 4 or set(logical) != set(TARGETS):
        raise Refusal('Unexpected removal summary')
    if index >= len(lines) or not re.fullmatch(
            r'0 upgraded, 0 newly installed, 4 to remove and [0-9]+ not upgraded\.',
            lines[index]):
        raise Refusal('Install/upgrade/download/unknown summary')
    removed = []
    for line in lines[index + 1:]:
        match = re.fullmatch(r'(?:Remv|Purg) (' + PACKAGE + r') \[(' + VERSION + r')\]', line)
        if match is None:
            raise Refusal('Unknown/Conf/Inst/download/extra removal operation')
        name = resolve_identity(match[1], rows)
        if name not in TARGETS:
            raise Refusal('Unknown/Conf/Inst/download/extra removal operation')
        if rows[name][0] != match[2] or name in removed:
            raise Refusal('Version or duplicate removal drift')
        removed.append(name)
    if len(removed) != 4 or set(removed) != set(TARGETS):
        raise Refusal('Incomplete removal plan')
    return tuple(removed)


def reduce_image(adapter):
    """Actual control logic, injectable for inert tests; no shell or input commands."""
    before_raw = adapter.command(QUERY, 'inventory-before')
    before = inventory(before_raw)
    guard_packages(before)
    if adapter.command(('/usr/bin/dpkg', '--audit'), 'audit-before'):
        raise Refusal('Preexisting dpkg audit findings')
    manifest = adapter.manifest(tuple(sorted(set(before) - set(TARGETS))))
    parse_plan(adapter.command(SIMULATE, 'simulate'), before)
    # Exactly one destructive command, only after all preflight checks succeeded.
    adapter.command(PURGE, 'purge-once')
    after = inventory(adapter.command(QUERY, 'inventory-after'))
    expected = {key: value for key, value in before.items() if key not in TARGETS}
    if after != expected:
        raise Refusal('Post-purge package/dependency/status drift')
    if adapter.command(('/usr/bin/dpkg', '--audit'), 'audit-after'):
        raise Refusal('Post-purge dependency audit findings')
    if adapter.manifest(tuple(sorted(after))) != manifest:
        raise Refusal('Protected package/Python/app/wheel file drift')
    return {'state':'EXPERIMENTAL_REDUCTION_OBSERVED_NOT_SECURITY_ACCEPTANCE',
            'removed':list(TARGETS), 'remaining_packages':len(after),
            'protected_manifest_sha256':manifest, 'security_acceptance':False,
            'gcc_header_Perl_consumer_findings':'OPEN_NOT_WAIVED'}


class NativeBuildAdapter:
    """Closed native commands: only future network-disabled candidate Docker RUN."""

    def __init__(self):
        self.started = time.monotonic()
        self.deadline = self.started + 180
        self.sequence = 0
        self.purge_attempted = False
        self.receipts = Path('/reduction35-evidence')
        self.receipts.mkdir(mode=0o700)  # Existing directory refuses, no adoption.

    def tick(self):
        if time.monotonic() > self.deadline:
            raise Refusal('Shared build helper deadline UNKNOWN')

    def command(self, argv, stage):
        self.tick()
        fixed = (QUERY, SIMULATE, PURGE, ('/usr/bin/dpkg','--audit'))
        listing = (len(argv) >= 3 and argv[:2] == ('/usr/bin/dpkg-query','-L')
                   and all(re.fullmatch(PACKAGE, name) for name in argv[2:]))
        if argv not in fixed and not listing:
            raise Refusal('Unadmitted command')
        if argv == PURGE:
            if self.purge_attempted:
                raise Refusal('Purge consumed; never retry')
            self.purge_attempted = True
        self.sequence += 1
        try:
            completed = subprocess.run(argv, capture_output=True, check=False,
                                       timeout=max(0.001,self.deadline-time.monotonic()),
                                       env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin',
                                            'LC_ALL':'C','DEBIAN_FRONTEND':'noninteractive'})
            out, err, code = completed.stdout, completed.stderr, completed.returncode
        except subprocess.TimeoutExpired as error:
            out, err, code = error.stdout or b'', error.stderr or b'', None
        # Original complete return precedes all exit, deadline, size and parse guards.
        base = self.receipts / f'{self.sequence:03d}-{stage}'
        base.with_suffix('.stdout').write_bytes(out)
        base.with_suffix('.stderr').write_bytes(err)
        base.with_suffix('.json').write_text(json.dumps(
            {'argv':argv,'exit':code,'stdout_bytes':len(out),'stderr_bytes':len(err),
             'stdout_sha256':hashlib.sha256(out).hexdigest(),
             'stderr_sha256':hashlib.sha256(err).hexdigest()})+'\n')
        return checked_return(out, err, code, self.deadline, time.monotonic())

    def manifest(self, packages):
        raw = self.command(('/usr/bin/dpkg-query','-L',*packages), 'protected-paths')
        paths = set(raw.decode('utf-8',errors='strict').splitlines())
        # Include application and interpreter/wheels not owned by Debian packages.
        for root in ('/app','/usr/local/lib/python3.12','/usr/local/bin'):
            for directory, dirs, files in os.walk(root, followlinks=False):
                self.tick()
                paths.add(directory)
                paths.update(str(Path(directory)/name) for name in dirs + files)
                if len(paths) > MAX_FILES:
                    raise Refusal('Manifest completeness bound')
        digest = hashlib.sha256()
        total = 0
        for path in sorted(paths):
            self.tick()
            if not path.startswith('/') or '..' in Path(path).parts:
                raise Refusal('Unrepresentable owned file path')
            p = Path(path)
            info = p.lstat()
            row = {'path':path,'mode':info.st_mode,'uid':info.st_uid,'gid':info.st_gid}
            if stat.S_ISLNK(info.st_mode):
                row['link'] = os.readlink(p)
            elif stat.S_ISREG(info.st_mode):
                if info.st_size > 33554432:
                    raise Refusal('Per-file manifest byte bound')
                with p.open('rb') as stream:
                    h = hashlib.sha256()
                    while True:
                        chunk = stream.read(65536)
                        if not chunk:
                            break
                        total += len(chunk)
                        self.tick()
                        if total > MAX_HASH_BYTES:
                            raise Refusal('Manifest aggregate byte bound')
                        h.update(chunk)
                after = p.lstat()
                fields = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid',
                          'st_size', 'st_mtime_ns', 'st_ctime_ns')
                if any(getattr(after, key) != getattr(info, key) for key in fields):
                    raise Refusal('Owned file changed during hashing')
                row['sha256'] = h.hexdigest()
            elif not stat.S_ISDIR(info.st_mode):
                raise Refusal('Unsupported owned file type')
            digest.update((json.dumps(row,sort_keys=True)+'\n').encode())
        return digest.hexdigest()


def main():
    if os.getuid() != 0 or not Path('/app/requirements-runtime.txt').is_file():
        raise Refusal('Only isolated root image build with application preimage')
    adapter = NativeBuildAdapter()
    result = reduce_image(adapter)
    adapter.tick()
    (adapter.receipts/'result.json').write_text(json.dumps(result,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__ == '__main__':
    main()
