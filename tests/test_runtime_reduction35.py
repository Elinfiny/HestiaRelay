"""Six inert cases for the actual experimental helper; never native APT qualification."""

import importlib.util
import json
import sys
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'experiments/runtime_reduction35/prepare_runtime.py'
SPEC = importlib.util.spec_from_file_location('reduction35_test_source', SOURCE)
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)
ACTIVE = [False]


def deny_native(event, args):
    if ACTIVE[0] and (event == 'open' or event.startswith(
            ('subprocess.', 'os.', 'socket.', 'ctypes.', 'fcntl.'))):
        raise AssertionError('Real native boundary attempted during inert fixture')


sys.addaudithook(deny_native)


def rows():
    result = {}
    for name in HELPER.TARGETS + HELPER.REQUIRED:
        result[name] = ['1.0', 'amd64', 'ii ', '', '', '', '']
    result['libgcc-s1'][5] = 'gcc-14-base (= 1.0)'
    result['libstdc++6'][5] = 'gcc-14-base (= 1.0), libgcc-s1 (>= 1.0)'
    result['apt'][5] = 'libapt-pkg7.0 (= 1.0), libstdc++6 (>= 1.0)'
    return result


def encode(records):
    return ''.join('\t'.join([k, *v]) + '\n' for k, v in records.items()).encode()


def plan():
    return ('Reading package lists...\nBuilding dependency tree...\n'
            'Reading state information...\nThe following packages will be REMOVED:\n'
            '  apt* libapt-pkg7.0* sqv* libstdc++6*\n'
            '0 upgraded, 0 newly installed, 4 to remove and 0 not upgraded.\n'
            + ''.join(f'Purg {name} [1.0]\n' for name in HELPER.TARGETS)).encode()


class FakeAPT:
    def __init__(self, mode='valid'):
        self.mode = mode
        self.calls = []
        self.originals = []
        self.before = rows()
        if mode == 'essential':
            self.before['apt'][3] = 'yes'
        self.purges = 0

    def command(self, argv, stage):
        self.calls.append((argv, stage))
        out, err, code, now = b'', b'', 0, 0
        if stage == 'inventory-before':
            out = encode(self.before)
        elif stage == 'inventory-after':
            out = encode({k:v for k,v in self.before.items() if k not in HELPER.TARGETS})
        elif stage == 'simulate':
            out = plan()
            if self.mode == 'extra':
                out += b'Remv libgcc-s1 [1.0]\n'
            if self.mode == 'solver':
                out += b'Inst libc6 [1.0]\nConf libc6\nNeed to get 1 MB\nUNKNOWN solver\n'
            if self.mode == 'late':
                now = 181
            if self.mode == 'nonzero':
                code, err = 1, b'synthetic native failure UNKNOWN'
        elif stage == 'purge-once':
            if argv != HELPER.PURGE or self.purges:
                raise AssertionError('Unexpected/repeated destructive command')
            self.purges += 1
        elif stage not in ('audit-before', 'audit-after'):
            raise AssertionError('Unrecognized fixture command')
        # Immediate actual fixture originals precede every accept/refusal guard.
        self.originals.append({'stage':stage,'stdout':out.decode(),'stderr':err.decode(),
                               'exit':code,'clock':now})
        return HELPER.checked_return(out, err, code, 180, now)

    def manifest(self, packages):
        self.calls.append(('manifest', packages))
        return 'inert-public-file-manifest-identical'


class RuntimeReduction35Tests(unittest.TestCase):
    def exercise(self, mode):
        adapter = FakeAPT(mode)
        ACTIVE[0] = True
        try:
            if mode == 'valid':
                result = HELPER.reduce_image(adapter)
                self.assertEqual(result['removed'], list(HELPER.TARGETS))
                self.assertFalse(result['security_acceptance'])
                self.assertEqual(adapter.purges, 1)
                self.assertEqual(adapter.calls[-1][0], 'manifest')
            else:
                with self.assertRaises(HELPER.Refusal):
                    HELPER.reduce_image(adapter)
                self.assertEqual(adapter.purges, 0)
                self.assertNotIn('inventory-after', [s for a,s in adapter.calls])
                self.assertEqual(adapter.calls[-1][1],
                                 'inventory-before' if mode == 'essential' else 'simulate')
            if mode == 'late':
                self.assertEqual(adapter.originals[-1]['clock'], 181)
                self.assertTrue(adapter.originals[-1]['stdout'])
            if mode == 'nonzero':
                self.assertEqual(adapter.originals[-1]['exit'], 1)
                self.assertIn('UNKNOWN', adapter.originals[-1]['stderr'])
        finally:
            ACTIVE[0] = False
        print(json.dumps({'case':mode,'status':'PASS','purge_calls':adapter.purges,
                          'calls':adapter.calls,'original_receipts':adapter.originals,
                          'scope':'INERT_ONLY_NOT_NATIVE_APT_OR_SECURITY_PROOF'}), flush=True)

    def test_valid_exact_plan(self):
        self.exercise('valid')

    def test_extra_protected_removal(self):
        self.exercise('extra')

    def test_essential_target(self):
        self.exercise('essential')

    def test_install_download_unknown_solver(self):
        self.exercise('solver')

    def test_shared_deadline_failstop(self):
        self.exercise('late')

    def test_original_nonzero_unknown_failstop(self):
        self.exercise('nonzero')


if __name__ == '__main__':
    unittest.main(verbosity=2)
