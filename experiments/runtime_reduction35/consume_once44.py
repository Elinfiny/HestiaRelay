"""One fixed future POST, closed originals guard; import has no credential/network IO."""
import hashlib
import http.client
import json
import math
import os
import re
import ssl
import time
from pathlib import Path

HOST = 'api.github.com'
PORT = 443
REPOSITORY = 'Elinfiny/HestiaRelay'
BRANCH = 'review/hestia-runtime-reduction39-20261016'
REF = 'refs/tags/HESTIA-RUNTIME-REDUCTION35-20261015-ONCE'
ENDPOINT = '/repos/Elinfiny/HestiaRelay/git/refs'
MAX_BODY = 65536
MAX_REQUESTED = 65537
PUBLIC_CAP = 4096
USER_AGENT = 'HestiaRelay'


def validate(binding, token):
    keys = {'repository', 'head', 'run_id', 'run_attempt', 'event', 'head_ref'}
    if not isinstance(binding, dict) or set(binding) != keys:
        raise ValueError('Invalid binding')
    if (binding['repository'] != REPOSITORY or binding['event'] != 'pull_request'
            or binding['head_ref'] != BRANCH or binding['run_attempt'] != '1'):
        raise ValueError('Unsupported selector')
    if not isinstance(binding['head'], str) or not re.fullmatch(r'[0-9a-f]{40}', binding['head']):
        raise ValueError('Invalid head')
    if not isinstance(binding['run_id'], str) or not re.fullmatch(r'[1-9][0-9]{0,23}', binding['run_id']):
        raise ValueError('Invalid run')
    if (not isinstance(token, str) or not 1 <= len(token) <= 4096
            or not token.isascii() or any(c.isspace() for c in token)):
        raise ValueError('Missing protected credential')


def error_class(error):
    name = type(error).__name__
    return name if name in {'IncompleteRead', 'OSError', 'TimeoutError', 'ValueError',
                            'RuntimeError', 'HTTPException', 'OverflowError'} else 'EXCEPTION'


def unique_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def refusal_diagnostic(raw, status, complete):
    """Enum only from already owned bounded bytes; no reflected message or URL."""
    code = 'UNCLASSIFIED'
    if not complete or not isinstance(raw, bytes) or len(raw) > MAX_BODY:
        return {'code': code}
    try:
        doc = unique_json(raw)
        if (not isinstance(doc, dict) or set(doc)-{'message', 'documentation_url', 'status'}
                or not isinstance(doc.get('message'), str) or len(doc['message']) > 1024):
            return {'code': code}
        if 'status' in doc and doc['status'] not in (status, str(status)):
            return {'code': code}
        if 'documentation_url' in doc and doc['documentation_url'] not in (
                'https://docs.github.com/rest/git/refs#create-a-reference',
                'https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api'):
            return {'code': code}
        code = ('USER_AGENT_MENTIONED' if 'user-agent' in doc['message'].casefold()
                else 'GENERIC_HTTP_REFUSAL')
    except Exception:
        pass
    return {'code': code}


class NativeHTTPS:
    """Public will_close contract: persistent response belongs to connection;
    detached response belongs to wrapper. Each designated owner called once.
    Socket timeouts cooperate; DNS/kernel IO/backend hard stop is NOT proved.
    """
    host = HOST
    port = PORT

    def __init__(self, remaining, connection_factory=http.client.HTTPSConnection,
                 context_factory=ssl.create_default_context):
        self.connection = None
        self.original_response = None
        self.detached = False
        self.closed = False
        self.cleanup_originals = []
        context = context_factory()
        if context.check_hostname is not True or context.verify_mode != ssl.CERT_REQUIRED:
            raise ValueError('Verified TLS required')
        self.connection = connection_factory(HOST, PORT, timeout=remaining, context=context)
        self.connection.set_debuglevel(0)

    def timeout(self, remaining):
        self.connection.timeout = remaining
        if self.connection.sock is not None:
            self.connection.sock.settimeout(remaining)

    def request(self, body, token):
        self.connection.request('POST', ENDPOINT, body=body,
            headers={'User-Agent': USER_AGENT, 'Authorization': 'Bearer '+token, 'Accept': 'application/vnd.github+json',
                     'Content-Type': 'application/json', 'X-GitHub-Api-Version': '2022-11-28'})

    def response(self):
        response = self.connection.getresponse()
        self.original_response = response  # Before ownership/deadline/schema qualification.
        self.detached = response.will_close is True
        return response

    def close(self):
        if self.closed:
            raise RuntimeError('Owner cleanup already attempted')
        self.closed = True
        # A detached response is no longer closed by HTTPConnection.close().
        # getresponse may internally close the connection during this transfer;
        # that is distinct from this one wrapper-level connection cleanup call.
        owners = []
        if self.detached and self.original_response is not None:
            owners.append(('DETACHED_RESPONSE_CLOSE', self.original_response))
        if self.connection is not None:
            owners.append(('CONNECTION_CLOSE', self.connection))
        for name, owner in owners:
            try:
                owner.close()
            except Exception as error:
                self.cleanup_originals.append((name, error))
        return self.cleanup_originals


def consume(binding, token, factory=NativeHTTPS, clock=time.monotonic):
    # Holders exist BEFORE even the initial clock call. Originals never leave memory.
    private = {'connection': None, 'response': None, 'statuses': [], 'chunks': [],
               'clocks': [], 'clock_exceptions': [], 'primary_exceptions': [],
               'cleanup_exceptions': []}
    receipt = {'schema': 'HESTIA_ONCE38_V1', 'state': 'UNKNOWN',
               'post_allowance_consumed': False, 'status': None, 'stages': [],
               'first_unknown': None, 'cleanup_errors': [], 'ref': REF,
               'context': 'CALLER_CONTEXT_REQUIRES_EXTERNAL_ADMISSION',
               'original_retention': 'PRIVATE_IN_MEMORY_ONLY_NOT_DURABLE_BODY_PROOF',
               'deadline_scope': 'COOPERATING_TIMEOUTS_RETURN_GUARDS_NOT_DNS_KERNEL_BACKEND_STOP'}
    owned, projection = None, None
    qualified, qualified_count, requested = [], 0, 0
    previous, started, deadline = None, None, None
    phase = 'INITIAL_CLOCK'
    complete_body = False

    def unknown(where, error, cleanup=False):
        item = {'stage': where, 'class': error_class(error)}
        private['cleanup_exceptions' if cleanup else 'primary_exceptions'].append(error)
        if cleanup:
            receipt['cleanup_errors'].append(item)
        if receipt['first_unknown'] is None:
            receipt['first_unknown'] = item

    def sample():
        nonlocal previous
        try:
            original = clock()
        except Exception as error:
            private['clock_exceptions'].append(error)
            raise
        private['clocks'].append(original)  # Before type, finite or monotonic checks.
        if type(original) not in (int, float):
            raise ValueError('Clock type')
        value = float(original)
        if not math.isfinite(value) or (previous is not None and value < previous):
            raise ValueError('Clock finite monotonic contract')
        previous = value
        return value

    def remaining():
        value = deadline-sample()
        if value <= 0:
            raise TimeoutError('Absolute deadline expired')
        return value

    def retain_chunk(original):
        nonlocal qualified_count
        private['chunks'].append(original)  # Before any operation on the original.
        if not isinstance(original, bytes):
            raise ValueError('Chunk type')
        capacity = MAX_BODY-qualified_count
        prefix = original[:capacity]
        qualified.append(prefix)
        qualified_count += len(prefix)
        if len(original) > capacity:
            raise ValueError('Body cap')

    try:
        started = sample()
        deadline = started+15.0
        if not math.isfinite(deadline):
            raise ValueError('Deadline finite contract')
        validate(binding, token)
        receipt.update(head=binding['head'], run_id=binding['run_id'])
        phase = 'PRE_REQUEST'
        receipt['stages'].append(phase)
        owned = factory(remaining())
        private['connection'] = owned
        phase = 'CONNECTION_RETURN'
        remaining()
        if owned.host != HOST or owned.port != PORT:
            raise ValueError('Exact endpoint required')
        body = json.dumps({'ref': REF, 'sha': binding['head']}, separators=(',', ':')).encode()
        owned.timeout(remaining())
        phase = 'PRE_INVOKE'
        remaining()
        receipt['stages'].append(phase)
        receipt['post_allowance_consumed'] = True
        owned.request(body, token)  # Only POST; allowance consumed before invocation.
        phase = 'POST_RETURN'
        receipt['stages'].append(phase)
        remaining()
        owned.timeout(remaining())
        phase = 'RESPONSE_RETURN'
        response = owned.response()
        private['response'] = response
        status = response.status
        private['statuses'].append(status)
        if type(status) is not int or not 100 <= status <= 599:
            raise ValueError('Status type')
        receipt['status'] = status
        remaining()
        while True:
            owned.timeout(remaining())
            phase = 'READ_RETURN'
            count = min(16384, MAX_REQUESTED-requested)
            if count <= 0:
                raise ValueError('Read request cap')
            requested += count
            try:
                original = response.read(count)
            except http.client.IncompleteRead as error:
                unknown(phase, error)  # Preserve original first failure before partial guards.
                retain_chunk(error.partial)
                remaining()
                raise
            retain_chunk(original)
            remaining()
            if not original:
                complete_body = True
                break
        phase = 'HTTP_STATUS'
        if status != 201:
            raise ValueError('Non-201 refuses without retry/follow-up')
        phase = 'BODY_SCHEMA'
        doc = unique_json(b''.join(qualified))
        if not isinstance(doc, dict) or set(doc)-{'ref', 'node_id', 'url', 'object'}:
            raise ValueError('Response schema')
        obj = doc.get('object')
        if (doc.get('ref') != REF or not isinstance(obj, dict)
                or set(obj)-{'sha', 'type', 'url'} or obj.get('sha') != binding['head']
                or obj.get('type') != 'commit'):
            raise ValueError('Fixed response source')
        projection = {'ref': REF, 'sha': binding['head'], 'type': 'commit'}
        remaining()
    except Exception as error:
        if not private['primary_exceptions'] or private['primary_exceptions'][-1] is not error:
            unknown(phase, error)
    finally:
        if owned is not None:
            try:
                remaining()
            except Exception as error:
                unknown('PRE_CLOSE_CLOCK', error, cleanup=True)
            receipt['stages'].append('PRE_CLOSE_ONCE')
            try:
                errors = owned.close()
                if errors:
                    for name, error in errors:
                        unknown(name, error, cleanup=True)
            except Exception as error:
                unknown('CLOSE_RETURN', error, cleanup=True)
            try:
                remaining()
            except Exception as error:
                unknown('CLEANUP_CLOCK', error, cleanup=True)
    # Digest ONLY separately qualified bounded bytes, never join arbitrary private originals.
    receipt['body_bytes'] = qualified_count
    receipt['body_sha256'] = hashlib.sha256(b''.join(qualified)).hexdigest()
    receipt['body_coverage'] = ('COMPLETE_BOUNDED_BYTE_BODY' if complete_body
                              else 'QUALIFIED_BYTE_PREFIX_ONLY_NOT_FULL_INVALID_BODY')
    if receipt['status'] is not None and receipt['status'] != 201:
        receipt['public_diagnostic'] = refusal_diagnostic(
            b''.join(qualified), receipt['status'], complete_body)
    try:
        if deadline is not None:
            remaining()
    except Exception as error:
        unknown('FINAL_CLOCK', error)
    if receipt['first_unknown'] is None and projection is not None:
        receipt.update(state='CREATED_EXACT_FIXED_REF', public_projection=projection)
    if len(json.dumps(receipt, sort_keys=True).encode()) > PUBLIC_CAP:
        receipt = {'schema': 'HESTIA_ONCE38_V1', 'state': 'UNKNOWN',
                   'post_allowance_consumed': receipt['post_allowance_consumed'],
                   'first_unknown': {'stage': 'PUBLIC_CAP', 'class': 'ValueError'}}
    return receipt, private


def main():
    # Inert private candidate: refuse before environment, file or credential IO.
    print(json.dumps({'schema': 'HESTIA_ONCE44_PRIVATE_V1',
                      'state': 'NATIVE44_NOT_ADMITTED'}, sort_keys=True))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
