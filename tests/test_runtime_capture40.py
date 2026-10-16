"""Four methods, eight subcases, exactly three bounded real helper children."""
import hashlib
import importlib.util
import json
import pathlib
import sys
import tempfile
import time
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('capture40', ROOT/'experiments/runtime_reduction35/bounded_capture40.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
REAL = []


def audit(event, args):
    if event.startswith('socket.') or event in {'os.system', 'os.exec', 'os.posix_spawn'}:
        raise RuntimeError('Unadmitted native effect')
    if event == 'subprocess.Popen':
        argv = tuple(args[1])
        if argv[:4] != (sys.executable, '-I', '-B', '-c') or len(REAL) >= 3:
            raise RuntimeError('Only three exact fixture child slots')
        REAL.append(argv)

sys.addaudithook(audit)


class Capture40(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        assert len(REAL) == 3

    def emit(self, name, subcases, rec=None):
        print(json.dumps({'case': name, 'subcases': subcases, 'status': 'PASS',
                          'receipt': rec, 'real_children_so_far': len(REAL)}, sort_keys=True))

    def blocked(self, session):
        before = len(REAL)
        result = session.run((sys.executable, '-I', '-B', '-c', 'raise SystemExit(99)'), 'must-not-start')
        self.assertEqual(result['receipt']['first_unknown']['stage'], 'PRIOR_UNKNOWN')
        self.assertEqual(result['receipt']['spawn_count'], 0)
        self.assertEqual(len(REAL), before)

    def test_happy_real_finite_pipes(self):
        session = M.CaptureSession(time.monotonic()+2, allow_kill=True)
        script = 'import sys;sys.stdout.buffer.write(b"happy-out\\n");sys.stderr.buffer.write(b"happy-err\\n")'
        result = session.run((sys.executable, '-I', '-B', '-c', script), 'happy', limit=1,
                             stdout_cap=4096, stderr_cap=4096)
        rec = result['receipt']
        self.assertEqual(rec['status'], 'PASS')
        self.assertEqual(rec['exit'], 0)
        self.assertTrue(rec['actual_terminal'])
        self.assertEqual(rec['spawn_count'], 1)
        for name, raw in [('stdout', b'happy-out\n'), ('stderr', b'happy-err\n')]:
            self.assertEqual(result[name], raw)
            self.assertTrue(rec[name]['eof'] and rec[name]['full_original'])
            self.assertEqual(rec[name]['observed_sha256'], hashlib.sha256(raw).hexdigest())
        self.emit('happy-real-finite-pipes', 1, rec)

    def test_overflow_real_8192_max(self):
        session = M.CaptureSession(time.monotonic()+2, allow_kill=True)
        script = 'import sys,time;sys.stdout.buffer.write(b"x"*8192);sys.stdout.flush();time.sleep(0.2)'
        result = session.run((sys.executable, '-I', '-B', '-c', script), 'overflow', limit=1,
                             stdout_cap=4096, stderr_cap=4096)
        rec = result['receipt']
        self.assertEqual(rec['status'], 'UNKNOWN')
        self.assertEqual(rec['first_unknown']['stage'], 'CAPTURE')
        self.assertEqual(result['stdout'], b'x'*4096)
        self.assertEqual(rec['stdout']['observed_bytes'], 4097)
        self.assertFalse(rec['stdout']['full_original'])
        self.assertTrue(rec['actual_terminal'])
        self.assertLessEqual(rec['terminate_count'], 1)
        self.assertLessEqual(rec['kill_count'], 1)
        self.blocked(session)
        self.emit('overflow-real-cap4096-child8192', 1, rec)

    def test_short_real_deadline_cleanup(self):
        session = M.CaptureSession(time.monotonic()+1, allow_kill=True)
        script = 'import time;time.sleep(1)'
        result = session.run((sys.executable, '-I', '-B', '-c', script), 'timeout', limit=0.2,
                             stdout_cap=4096, stderr_cap=4096)
        rec = result['receipt']
        self.assertEqual(rec['status'], 'UNKNOWN')
        self.assertEqual(rec['first_unknown']['class'], 'TimeoutError')
        self.assertTrue(rec['actual_terminal'])
        self.assertEqual(rec['terminate_count'], 1)
        self.assertLessEqual(rec['kill_count'], 1)
        self.assertLessEqual(rec['wait_calls'], 2)
        self.blocked(session)
        self.emit('short-real-deadline-cleanup', 1, rec)

    def test_fake_sticky_and_bounded_files(self):
        # Five synthetic subcases; zero extra real helper children.
        before = len(REAL)
        bad = float('nan'); spawns = []
        session = M.CaptureSession(10.0, clock=lambda: bad,
                                   popen=lambda *a, **k: spawns.append(a))
        result = session.run(('fixed-fixture',), 'invalid-clock')
        self.assertEqual(result['receipt']['spawn_count'], 0)
        self.assertIs(session.last_clock_original, bad)
        self.assertFalse(spawns)
        self.blocked(session)
        cleanup = OSError('synthetic pipe cleanup')
        class Pipe:
            def __init__(self, fd): self.fd, self.closes = fd, 0
            def fileno(self): return self.fd
            def close(self):
                self.closes += 1
                if self.fd == 110: raise cleanup
        class Child:
            stdout, stderr = Pipe(110), Pipe(111)
            def wait(self, timeout): return 7
            def poll(self): return 7
        child = Child(); calls = []
        class Selector:
            def __init__(self): self.items = {}
            def register(self, pipe, event, name):
                self.items[pipe.fd] = types.SimpleNamespace(fileobj=pipe, data=name)
            def get_map(self): return self.items
            def select(self, timeout): return [(x, 1) for x in list(self.items.values())]
            def unregister(self, pipe): del self.items[pipe.fd]
            def close(self): pass
        chunks = {110: [b'out', b''], 111: [b'err', b'']}
        def popen(*args, **kwargs):
            calls.append(args); return child
        session = M.CaptureSession(10.0, clock=lambda: 0.0, popen=popen,
            selector_factory=Selector, reader=lambda fd, n: chunks[fd].pop(0),
            nonblocking=lambda fd, blocking: None)
        result = session.run(('fixed-fixture',), 'fake-nonzero')
        rec = result['receipt']
        self.assertEqual(rec['first_unknown']['stage'], 'WAIT_RETURN')
        self.assertEqual(rec['exit'], 7)
        self.assertEqual(len(calls), 1)
        self.assertIs(session.cleanup_originals[0], cleanup)
        self.assertEqual(child.stdout.closes, 1)
        self.assertEqual(child.stderr.closes, 1)
        primary = session.primary_original
        self.blocked(session)
        self.assertIs(session.primary_original, primary)
        self.assertEqual(len(calls), 1)
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory); (root/'finite').write_bytes(b'finite')
            self.assertEqual(M.bounded_file(root, root/'finite', 8), b'finite')
            (root/'overflow').write_bytes(b'overflow!')
            with self.assertRaises(ValueError): M.bounded_file(root, root/'overflow', 8)
            with self.assertRaises(ValueError): M.bounded_file(root, root/'..'/'escape', 8)
        self.assertEqual(len(REAL), before)
        self.emit('fake-clock-nonzero-cleanup-and-files', 5, rec)


if __name__ == '__main__':
    unittest.main()
