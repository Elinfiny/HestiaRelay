"""Bounded Linux pipe capture for fixed developer-owned argv; no shell or retries.

Absolute suite deadline is supplied once. Socket/kernel/backend hard stop is not
claimed. Prefixes are complete originals only after bounded EOF and actual terminal.
"""
import hashlib
import math
import os
import pathlib
import selectors
import stat
import subprocess
import time


def bounded_file(root, path, cap):
    """Regular no-symlink file under an existing trusted root; allocate at most cap+1."""
    root = pathlib.Path(root).resolve(strict=True)
    path = pathlib.Path(path)
    if not path.is_absolute():
        path = path.absolute()
    relative = path.relative_to(root)
    if not relative.parts or any(p in ('', '.', '..') for p in relative.parts):
        raise ValueError('File containment')
    current = root
    for part in relative.parts:
        current = current / part
        if stat.S_ISLNK(current.lstat().st_mode):
            raise ValueError('Symlink refused')
    # O_NOFOLLOW plus fd stat catches last-component substitution; parent path is
    # an explicitly trusted evidence root, not a hostile concurrent filesystem.
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > cap:
            raise ValueError('Regular file cap')
        parts, count = [], 0
        while count <= cap:
            original = os.read(fd, min(65536, cap + 1 - count))
            count += len(original)
            if count > cap:
                raise ValueError('File grew beyond cap')
            if not original:
                return b''.join(parts)
            parts.append(original)
    finally:
        os.close(fd)
    raise ValueError('Incomplete bounded file')


class CaptureSession:
    def __init__(self, deadline, *, allow_kill=False, clock=time.monotonic,
                 popen=subprocess.Popen, selector_factory=selectors.DefaultSelector,
                 reader=os.read, nonblocking=os.set_blocking):
        self.deadline, self.allow_kill, self.clock = deadline, allow_kill, clock
        self.popen, self.selector_factory = popen, selector_factory
        self.reader, self.nonblocking = reader, nonblocking
        self.blocked = False
        self.previous = None
        self.last_clock_original = None
        self.clock_error_original = None
        self.primary_original = None
        self.cleanup_originals = []

    def now(self):
        try:
            value = self.clock()
        except Exception as error:
            self.clock_error_original = error
            raise
        self.last_clock_original = value
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError('Clock type/finite')
        if self.previous is not None and value < self.previous:
            raise ValueError('Clock moved backward')
        self.previous = value
        return value

    def run(self, argv, label, *, limit=180, stdout_cap=16777216, stderr_cap=16777216):
        rec = {'schema': 'HESTIA_BOUNDED_CAPTURE40_V1', 'label': label,
               'status': 'UNKNOWN', 'first_unknown': None, 'cleanup': [],
               'spawn_count': 0, 'terminate_count': 0, 'kill_count': 0,
               'wait_calls': 0, 'exit': None, 'actual_terminal': False,
               'stages': [], 'deadline_scope': 'COOPERATING_IO_NOT_KERNEL_BACKEND_STOP'}
        buffers = {'stdout': bytearray(), 'stderr': bytearray()}
        counts = {'stdout': 0, 'stderr': 0}
        digests = {k: hashlib.sha256() for k in counts}
        eof = {k: False for k in counts}
        caps = {'stdout': stdout_cap, 'stderr': stderr_cap}
        child, selector = None, None
        pipes = {}
        phase, terminal_timely = 'PRE_REQUEST', False
        command_deadline = None

        def unknown(where, error, cleanup=False):
            item = {'stage': where, 'class': type(error).__name__
                    if type(error).__name__ in {'ValueError', 'TimeoutError', 'OSError',
                      'RuntimeError', 'TimeoutExpired', 'OverflowError'} else 'EXCEPTION'}
            if cleanup:
                self.cleanup_originals.append(error)
                rec['cleanup'].append(item)
            elif self.primary_original is None:
                self.primary_original = error
            if rec['first_unknown'] is None:
                rec['first_unknown'] = item
            self.blocked = True

        def remaining(end):
            value = end-self.now()
            if value <= 0:
                raise TimeoutError('Absolute deadline')
            return value

        if self.blocked:
            rec['first_unknown'] = {'stage': 'PRIOR_UNKNOWN', 'class': 'RuntimeError'}
            return {'receipt': rec, 'stdout': b'', 'stderr': b''}
        try:
            if (not isinstance(argv, (list, tuple)) or not argv
                    or any(not isinstance(a, str) or '\0' in a for a in argv)):
                raise ValueError('Fixed argv only')
            if (type(self.deadline) not in (int, float) or not math.isfinite(self.deadline)
                    or type(limit) not in (int, float) or not math.isfinite(limit) or limit <= 0
                    or any(type(v) is not int or not 0 < v <= 16777216 for v in caps.values())):
                raise ValueError('Deadline/cap contract')
            started = self.now()
            command_deadline = min(self.deadline, started+limit)
            room = remaining(command_deadline)
            # Cleanup time is reserved INSIDE this same command/suite window.
            capture_deadline = command_deadline-min(0.5, room*0.25)
            rec['stages'].append('PRE_INVOKE')
            phase = 'POST_RETURN'
            remaining(capture_deadline)
            rec['spawn_count'] = 1
            child = self.popen(tuple(argv), shell=False, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, close_fds=True)
            # The actual child and pipe handles are retained before post-return clock.
            pipes = {'stdout': child.stdout, 'stderr': child.stderr}
            rec['stages'].append(phase)
            remaining(capture_deadline)
            selector = self.selector_factory()
            for name, pipe in pipes.items():
                self.nonblocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, name)
            phase = 'CAPTURE'
            while selector.get_map():
                room = remaining(capture_deadline)
                for key, mask in selector.select(min(room, 0.05)):
                    name = key.data
                    # When prefix is full, read ONE byte to detect overflow; never
                    # append beyond its cap. No unbounded communicate/run/read.
                    amount = min(65536, max(1, caps[name]-len(buffers[name])))
                    original = self.reader(key.fileobj.fileno(), amount)
                    counts[name] += len(original)
                    digests[name].update(original)
                    capacity = caps[name]-len(buffers[name])
                    buffers[name].extend(original[:capacity])
                    # Prefix/count/digest recorded BEFORE clock/overflow qualification.
                    if counts[name] > caps[name]:
                        raise ValueError('Pipe overflow')
                    remaining(capture_deadline)
                    if not original:
                        eof[name] = True
                        selector.unregister(key.fileobj)
            phase = 'WAIT_RETURN'
            rec['wait_calls'] += 1
            code = child.wait(timeout=remaining(command_deadline))
            rec['exit'], rec['actual_terminal'] = code, True
            remaining(command_deadline)
            terminal_timely = True
            if code != 0:
                raise RuntimeError('Nonzero actual terminal')
        except Exception as error:
            unknown(phase, error)
        finally:
            if child is not None and not rec['actual_terminal']:
                # Only this returned owned child. Each signal is attempted once.
                try:
                    code = child.poll()
                    if code is not None:
                        rec['exit'], rec['actual_terminal'] = code, True
                    else:
                        remaining(command_deadline)
                        rec['terminate_count'] += 1
                        child.terminate()
                        try:
                            rec['wait_calls'] += 1
                            code = child.wait(timeout=min(0.1, remaining(command_deadline)))
                            rec['exit'], rec['actual_terminal'] = code, True
                        except subprocess.TimeoutExpired as error:
                            unknown('TERMINATE_WAIT', error, cleanup=True)
                            if self.allow_kill:
                                remaining(command_deadline)
                                rec['kill_count'] += 1
                                child.kill()
                                rec['wait_calls'] += 1
                                code = child.wait(timeout=remaining(command_deadline))
                                rec['exit'], rec['actual_terminal'] = code, True
                    remaining(command_deadline)
                except Exception as error:
                    unknown('OWN_CHILD_CLEANUP', error, cleanup=True)
            if selector is not None:
                try:
                    selector.close()
                except Exception as error:
                    unknown('SELECTOR_CLOSE', error, cleanup=True)
            for name, pipe in pipes.items():
                try:
                    pipe.close()
                except Exception as error:
                    unknown(name+'_CLOSE', error, cleanup=True)
        for name in counts:
            rec[name] = {'observed_bytes': counts[name], 'stored_bytes': len(buffers[name]),
                         'observed_sha256': digests[name].hexdigest(),
                         'prefix_sha256': hashlib.sha256(buffers[name]).hexdigest(),
                         'eof': eof[name], 'full_original': eof[name] and terminal_timely
                         and counts[name] <= caps[name], 'cap': caps[name]}
        if rec['first_unknown'] is None:
            try:
                remaining(command_deadline)
                rec['status'] = 'PASS'
            except Exception as error:
                unknown('FINAL_RETURN', error)
        return {'receipt': rec, 'stdout': bytes(buffers['stdout']),
                'stderr': bytes(buffers['stderr'])}
