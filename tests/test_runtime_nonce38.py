"""Admission39: eight methods/18 synthetic subcases on integrated changed source."""
import http.client
import importlib.util
import json
import pathlib
import ssl
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('once39', ROOT/'experiments/runtime_reduction35/consume_once38.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
ACTIVE = False
TOKEN = 'TEST_ONLY_NOT_CREDENTIAL'
BINDING = {'repository': M.REPOSITORY, 'head': 'a'*40, 'run_id': '123',
           'run_attempt': '1', 'event': 'pull_request', 'head_ref': M.BRANCH}
BODY = json.dumps({'ref': M.REF, 'object': {'sha': 'a'*40, 'type': 'commit'}}).encode()


def deny(event, args):
    if ACTIVE and (event.startswith(('socket.', 'subprocess.', 'os.system', 'os.exec', 'os.spawn'))
                   or event in {'open', 'os.remove', 'os.rename', 'os.mkdir'}):
        raise RuntimeError('Synthetic fixture refuses native IO')

sys.addaudithook(deny)


class Clock:
    def __init__(self):
        self.value = 0.0
    def __call__(self):
        return self.value


class FakeConnection:
    host, port = M.HOST, M.PORT
    def __init__(self, clock, status=201, chunks=None, late=False, close_error=None):
        self.clock, self.status = clock, status
        self.chunks = list(chunks if chunks is not None else [BODY, b''])
        self.late, self.close_error = late, close_error
        self.requests, self.closes, self.requested = 0, 0, 0
    def timeout(self, value):
        assert 0 < value <= 15
    def request(self, body, token):
        self.requests += 1
        assert json.loads(body) == {'ref': M.REF, 'sha': 'a'*40}
        assert token == TOKEN
    def response(self):
        return self
    def read(self, count):
        self.requested += count
        assert self.requested <= 65537
        original = self.chunks.pop(0)
        if self.late:
            self.clock.value = 16.0
        if isinstance(original, Exception):
            raise original
        return original
    def close(self):
        self.closes += 1
        if self.close_error is not None:
            raise self.close_error
        return []


class Once39(unittest.TestCase):
    def call(self, connection, clock, factory=None):
        global ACTIVE
        ACTIVE = True
        try:
            receipt, private = M.consume(BINDING, TOKEN,
                factory=factory or (lambda remaining: connection), clock=clock)
        finally:
            ACTIVE = False
        public = json.dumps(receipt, sort_keys=True)
        self.assertLessEqual(len(public.encode()), 4096)
        for forbidden in [TOKEN, 'Authorization', 'PRIVATE_TEXT', 'PRIVATE_CLOSE', 'PRIVATE_RESPONSE', 'PRIVATE_CONNECTION', 'nan', 'Infinity']:
            self.assertNotIn(forbidden, public)
        if connection is not None:
            self.assertEqual(connection.requests, 1)
            self.assertEqual(connection.closes, 1)
            self.assertTrue(receipt['post_allowance_consumed'])
            self.assertIs(private['connection'], connection)
            self.assertIs(private['response'], connection)
        return receipt, private
    def emit(self, case, subcases, receipt=None):
        print(json.dumps({'case': case, 'subcases': subcases, 'status': 'PASS',
                          'receipt': receipt, 'scope': 'SYNTHETIC_NO_NATIVE_HTTP_TLS_AUTHORITY'}))
    def test_timely_201(self):
        c = Clock(); n = FakeConnection(c)
        r, p = self.call(n, c)
        self.assertEqual(r['state'], 'CREATED_EXACT_FIXED_REF')
        self.assertEqual(b''.join(p['chunks']), BODY)
        self.assertEqual(r['public_projection']['sha'], 'a'*40)
        self.emit('timely201', 1, r)
    def test_422_original(self):
        c = Clock(); raw = b'PRIVATE_422'; n = FakeConnection(c, 422, [raw, b''])
        r, p = self.call(n, c)
        self.assertEqual(r['state'], 'UNKNOWN')
        self.assertEqual(r['first_unknown']['stage'], 'HTTP_STATUS')
        self.assertIs(p['chunks'][0], raw)
        self.emit('422body', 1, r)
    def test_redirect_no_follow(self):
        c = Clock(); raw = b'PRIVATE_REDIRECT'; n = FakeConnection(c, 302, [raw, b''])
        r, p = self.call(n, c)
        self.assertEqual(r['state'], 'UNKNOWN')
        self.assertIs(p['chunks'][0], raw)
        self.emit('redirect-no-follow', 1, r)
    def test_late_201_retained(self):
        c = Clock(); raw = b'PRIVATE_LATE'; n = FakeConnection(c, chunks=[raw], late=True)
        r, p = self.call(n, c)
        self.assertEqual(r['state'], 'UNKNOWN')
        self.assertEqual(r['status'], 201)
        self.assertEqual(r['first_unknown']['stage'], 'READ_RETURN')
        self.assertIs(p['chunks'][0], raw)
        self.emit('late201', 1, r)
    def test_partial_read_close_error(self):
        c = Clock(); primary = http.client.IncompleteRead(b'PRIVATE_PARTIAL', 100)
        cleanup = OSError('PRIVATE_CLOSE'); n = FakeConnection(c, chunks=[primary], close_error=cleanup)
        r, p = self.call(n, c)
        self.assertEqual(r['state'], 'UNKNOWN')
        self.assertIs(p['primary_exceptions'][0], primary)
        self.assertIs(p['cleanup_exceptions'][0], cleanup)
        self.assertIs(p['chunks'][0], primary.partial)
        self.assertEqual(r['first_unknown']['class'], 'IncompleteRead')
        self.assertEqual(r['body_coverage'], 'QUALIFIED_BYTE_PREFIX_ONLY_NOT_FULL_INVALID_BODY')
        self.emit('partial-primary-cleanup', 1, r)
    def test_invalid_chunks_finalization(self):
        for original in [None, 7, 'PRIVATE_TEXT']:
            with self.subTest(kind=type(original).__name__):
                c = Clock(); n = FakeConnection(c, chunks=[original])
                r, p = self.call(n, c)
                self.assertEqual(r['state'], 'UNKNOWN')
                self.assertIs(p['chunks'][0], original)
                self.assertEqual(r['first_unknown'], {'stage': 'READ_RETURN', 'class': 'ValueError'})
                self.assertEqual(r['body_bytes'], 0)
                self.assertEqual(len(p['primary_exceptions']), 1)
        self.emit('invalid-chunks-finalization', 3)
    def test_clock_originals_no_next_effect(self):
        initial_error = OSError('PRIVATE_INITIAL_CLOCK')
        later_error = OSError('PRIVATE_LATER_CLOCK')
        originals = [None, True, float('nan'), float('inf'), initial_error,
                     float('nan'), -1.0, later_error]
        for index, original in enumerate(originals):
            with self.subTest(index=index):
                sequence = [original] if index < 5 else [0.0, 0.0, original]
                count = [0]; created = []
                def clock():
                    value = sequence.pop(0) if sequence else 0.0
                    if isinstance(value, Exception):
                        raise value
                    return value
                def factory(remaining):
                    count[0] += 1
                    n = FakeConnection(Clock()); created.append(n)
                    return n
                r, p = self.call(None, clock, factory)
                self.assertEqual(r['state'], 'UNKNOWN')
                self.assertFalse(r['post_allowance_consumed'])
                self.assertEqual(count[0], 0 if index < 5 else 1)
                if isinstance(original, Exception):
                    self.assertIs(p['clock_exceptions'][0], original)
                    self.assertIs(p['primary_exceptions'][0], original)
                else:
                    self.assertTrue(any(value is original for value in p['clocks']))
                for n in created:
                    self.assertEqual(n.requests, 0)
                    self.assertEqual(n.closes, 1)
        self.emit('clock-originals-no-next-effect', 8)
    def test_native_wrapper_owned_resources(self):
        for detached in [False, True]:
            with self.subTest(detached=detached):
                clock = Clock(); primary = OSError('PRIVATE_RESPONSE_CLOSE')
                secondary = OSError('PRIVATE_CONNECTION_CLOSE')
                class Response:
                    status = 201
                    will_close = detached
                    def __init__(self):
                        self.chunks = [BODY, b'']; self.closes = 0
                    def read(self, count):
                        return self.chunks.pop(0)
                    def close(self):
                        self.closes += 1
                        if detached:
                            raise primary
                response = Response()
                class Underlying:
                    sock = None
                    def __init__(self):
                        self.closes = 0; self.requests = 0; self.gets = 0
                        self.held = None
                    def set_debuglevel(self, value):
                        assert value == 0
                    def request(self, method, path, body, headers):
                        self.requests += 1
                        assert method == 'POST' and path == M.ENDPOINT
                        assert headers['Authorization'] == 'Bearer '+TOKEN
                    def getresponse(self):
                        self.gets += 1
                        if detached:
                            self.close()  # Synthetic public stdlib transfer contract.
                        else:
                            self.held = response
                        return response
                    def close(self):
                        self.closes += 1
                        held, self.held = self.held, None
                        if held is not None:
                            held.close()
                        if detached and self.closes == 2:
                            raise secondary
                underlying = Underlying(); wrappers = []
                class Context:
                    check_hostname = True
                    verify_mode = ssl.CERT_REQUIRED
                def make(remaining):
                    def connection_factory(host, port, **kwargs):
                        assert host == M.HOST and port == 443
                        assert isinstance(kwargs['context'], Context)
                        return underlying
                    n = M.NativeHTTPS(remaining, connection_factory, Context)
                    wrappers.append(n)
                    return n
                r, p = self.call(None, clock, make)
                self.assertEqual(underlying.requests, 1)
                self.assertEqual(underlying.gets, 1)
                self.assertEqual(response.closes, 1)
                self.assertEqual(underlying.closes, 2 if detached else 1)
                self.assertIs(p['response'], response)
                self.assertIs(wrappers[0].original_response, response)
                self.assertTrue(wrappers[0].closed)
                if detached:
                    self.assertEqual(r['state'], 'UNKNOWN')
                    self.assertIs(p['cleanup_exceptions'][0], primary)
                    self.assertIs(p['cleanup_exceptions'][1], secondary)
                else:
                    self.assertEqual(r['state'], 'CREATED_EXACT_FIXED_REF')
        self.emit('native-wrapper-persistent-detached-owners', 2)


if __name__ == '__main__':
    unittest.main()
