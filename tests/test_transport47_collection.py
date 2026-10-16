"""One guarded import boundary; never runs the already-qualified cleanup case."""
import argparse
import builtins
import contextlib
import hashlib
import http.client
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import ssl
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

HELPER_SOURCE_OVERRIDE = None
HELPER_SHA256 = 'bcf3fc19fe7e3f24c99adf0b92be7d0301a7ed9306ccd78fd9325d64fab2d066'
FINAL_TEST45_SHA256 = 'c67113a9280b32dafa286060622402afa01163e0b7e3cb490d873b413b825cd3'


class CollectionBoundary47(unittest.TestCase):
    def test_final_test45_import_has_no_effects(self):
        root = Path(__file__).resolve().parents[1]
        target = root/'tests/test_nonce_transport45_cleanup.py'
        helper = (Path(HELPER_SOURCE_OVERRIDE) if HELPER_SOURCE_OVERRIDE is not None
                  else root/'experiments/runtime_reduction35/consume_once44.py')
        raw, helper_raw = target.read_bytes(), helper.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), FINAL_TEST45_SHA256)
        self.assertEqual(len(helper_raw), 13399)
        self.assertEqual(hashlib.sha256(helper_raw).hexdigest(), HELPER_SHA256)
        name = 'hestia47_guarded_collection_target'
        module = types.ModuleType(name)
        module.__file__ = str(target)
        code = compile(raw, str(target), 'exec')
        effects = {}
        def forbidden(label):
            def reject(*args, **kwargs):
                effects[label] = effects.get(label, 0)+1
                raise AssertionError('IMPORT_EFFECT_FORBIDDEN_'+label)
            return reject
        class NoEnvironment:
            def __getattribute__(self, key):
                return forbidden('ENV')(key)
            def __getitem__(self, key):
                return forbidden('ENV')(key)
        # All stdlib dependencies above are preloaded before the effect guards.
        self.assertNotIn(name, sys.modules)
        sys.modules[name] = module
        try:
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(sys, 'argv', ('pytest', '--cov=hestiarelay')))
                stack.enter_context(patch.object(os, 'environ', NoEnvironment()))
                for owner, attr, label in [
                    (signal, 'alarm', 'TIMER'), (os, 'getenv', 'ENV'),
                    (builtins, 'open', 'FILE'), (Path, 'read_bytes', 'FILE'),
                    (Path, 'read_text', 'FILE'), (Path, 'open', 'FILE'),
                    (Path, 'resolve', 'PATH_RESOLVE'), (Path, 'stat', 'FILE'),
                    (socket, 'getaddrinfo', 'DNS'), (socket, 'create_connection', 'SOCKET'),
                    (socket.socket, 'connect', 'SOCKET'),
                    (ssl, 'create_default_context', 'SSL'),
                    (http.client, 'HTTPSConnection', 'HTTP'),
                    (subprocess, 'Popen', 'PROCESS'), (subprocess, 'run', 'PROCESS'),
                    (subprocess, 'call', 'PROCESS'), (subprocess, 'check_output', 'PROCESS'),
                    (os, 'system', 'PROCESS'),
                    (importlib.util, 'spec_from_file_location', 'HELPER_IMPORT'),
                    (unittest.TestCase, 'run', 'OLD_CASE_EXECUTION')]:
                    stack.enter_context(patch.object(owner, attr, forbidden(label)))
                exec(code, module.__dict__)
                suite = unittest.TestLoader().loadTestsFromModule(module)
                self.assertEqual(suite.countTestCases(), 1)
                cases = [case for child in suite for case in child]
                self.assertEqual(len(cases), 1)
                self.assertEqual(cases[0].id(), name+'.CleanupOwner45.'+
                                 'test_connection_owner_cleanup_retains_primary')
                self.assertEqual(module.HELPER_OVERRIDE, None)
                self.assertEqual(module.HELPER_SHA256, HELPER_SHA256)
            self.assertEqual(effects, {})
        finally:
            del sys.modules[name]
        print(json.dumps({'scenario':'FINAL45_NON_MAIN_IMPORT_BOUNDARY_47', 'status':'PASS',
            'loaded_entire_final_source':True, 'pytest_like_argv':True,
            'collected_class':'CleanupOwner45', 'methods_seen':1,
            'case45_executions':0, 'helper_executions':0, 'fakePOST':0,
            'guarded_effect_attempts':effects, 'actual_native_IO':0}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--helper-source')
    HELPER_SOURCE_OVERRIDE = parser.parse_args().helper_source
    signal.alarm(20)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(CollectionBoundary47))
    raise SystemExit(0 if result.wasSuccessful() else 2)
