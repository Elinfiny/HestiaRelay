"""One synthetic cleanup-owner scenario; no old test-suite import or native IO."""
import argparse
import hashlib
import http.client
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import ssl
import sys
import types
import unittest
from unittest.mock import patch

HELPER_OVERRIDE = None
HELPER_SHA256 = 'bcf3fc19fe7e3f24c99adf0b92be7d0301a7ed9306ccd78fd9325d64fab2d066'


def forbidden(*args, **kwargs):
    raise AssertionError('REAL_IO_FORBIDDEN')


class NoEnvironment:
    def __getattribute__(self, name):
        raise AssertionError('ENV_CREDENTIAL_READ_FORBIDDEN')
    def __getitem__(self, key):
        raise AssertionError('ENV_CREDENTIAL_READ_FORBIDDEN')


class CleanupOwner45(unittest.TestCase):
    def test_connection_owner_cleanup_retains_primary(self):
        source = (Path(HELPER_OVERRIDE) if HELPER_OVERRIDE is not None else
                  Path(__file__).resolve().parents[1] /
                  'experiments/runtime_reduction35/consume_once44.py')
        raw_source = source.read_bytes()
        self.assertEqual(len(raw_source), 13399)
        self.assertEqual(hashlib.sha256(raw_source).hexdigest(), HELPER_SHA256)
        spec = importlib.util.spec_from_file_location('transport44_for45', source)
        module = importlib.util.module_from_spec(spec)
        raw = b'{"message":"User-Agent required","status":"403"}'
        cleanup_error = OSError('SYNTHETIC_CONNECTION_CLOSE_45')
        constructions, requests, close_attempts = [], [], []
        context = types.SimpleNamespace(check_hostname=True, verify_mode=ssl.CERT_REQUIRED,
                                        synthetic_context=True)

        class Response:
            status = 403
            will_close = False
            reads = 0
            def read(self, count):
                self.reads += 1
                return raw if self.reads == 1 else b''

        response = Response()

        class Connection:
            sock = None
            def set_debuglevel(self, value):
                self.debug = value
            def request(self, *args, **kwargs):
                requests.append((args, kwargs))
            def getresponse(self):
                return response
            def close(self):
                close_attempts.append('connection_owner')
                raise cleanup_error

        connection = Connection()
        def connection_factory(host, port, **kwargs):
            constructions.append((host, port, kwargs))
            return connection

        with patch.object(os, 'environ', NoEnvironment()), patch.object(os, 'getenv', forbidden), \
                patch.object(socket, 'create_connection', forbidden), \
                patch.object(socket, 'getaddrinfo', forbidden), \
                patch.object(socket.socket, 'connect', forbidden), \
                patch.object(ssl, 'create_default_context', forbidden), \
                patch.object(http.client, 'HTTPSConnection', forbidden), \
                patch.object(Path, 'read_bytes', forbidden):
            spec.loader.exec_module(module)
            def factory(remaining):
                return module.NativeHTTPS(remaining, connection_factory=connection_factory,
                                          context_factory=lambda: context)
            binding = {'repository':module.REPOSITORY, 'head':'b'*40, 'run_id':'45',
                       'run_attempt':'1', 'event':'pull_request', 'head_ref':module.BRANCH}
            receipt, private = module.consume(binding, 'SYNTHETIC_FIXTURE_45',
                                              factory=factory, clock=lambda: 0.0)
        self.assertEqual(len(constructions), 1)
        self.assertEqual(constructions[0][0:2], ('api.github.com', 443))
        self.assertIs(constructions[0][2]['context'], context)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0][0], ('POST', module.ENDPOINT))
        self.assertEqual(close_attempts, ['connection_owner'])
        self.assertEqual(response.reads, 2)
        self.assertEqual(receipt['first_unknown'], {'stage':'HTTP_STATUS','class':'ValueError'})
        self.assertEqual(receipt['cleanup_errors'], [{'stage':'CONNECTION_CLOSE','class':'OSError'}])
        self.assertEqual(private['cleanup_exceptions'], [cleanup_error])
        self.assertIs(private['cleanup_exceptions'][0], cleanup_error)
        self.assertIsInstance(private['primary_exceptions'][0], ValueError)
        self.assertIsNot(private['primary_exceptions'][0], cleanup_error)
        self.assertIs(private['chunks'][0], raw)
        self.assertIs(private['response'], response)
        self.assertEqual(receipt['body_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(receipt['body_bytes'], len(raw))
        self.assertEqual(receipt['body_coverage'], 'COMPLETE_BOUNDED_BYTE_BODY')
        self.assertTrue(receipt['post_allowance_consumed'])
        self.assertEqual(receipt['state'], 'UNKNOWN')
        self.assertEqual(len(json.dumps(receipt).encode()) <= module.PUBLIC_CAP, True)
        print(json.dumps({'scenario':'45_CONNECTION_OWNER_CLEANUP_ONLY', 'status':'PASS',
            'synthetic':True, 'native_authority':False, 'fakePOST':len(requests),
            'connection_constructions':len(constructions), 'close_attempts':len(close_attempts),
            'first_unknown':receipt['first_unknown'], 'cleanup_errors':receipt['cleanup_errors'],
            'original_exception_identity':True, 'original_body_identity':True,
            'consumed':receipt['post_allowance_consumed'], 'state':receipt['state']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('helper_path', nargs='?')
    HELPER_OVERRIDE = parser.parse_args(sys.argv[1:]).helper_path
    signal.alarm(20)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(CleanupOwner45))
    raise SystemExit(0 if result.wasSuccessful() else 2)
