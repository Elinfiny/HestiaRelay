"""Bounded offline regressions for the two Python security fixes in the candidate."""

import base64
import io
import ssl
import sys
import zlib
from http.client import HTTPResponse

import jwt
import pytest
import urllib3
from cryptography.hazmat.primitives.asymmetric import ed448, ed25519
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
from urllib3.exceptions import ProtocolError
from urllib3.response import DeflateDecoder


def b64url(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def test_unsigned_jwt_payload_remains_supported_and_nested_payload_refuses_cleanly():
    assert jwt.decode("eyJhbGciOiJub25lIn0.eyJzdWIiOiJmaWN0aW9uYWwifQ.",
                      options={"verify_signature": False}) == {"sub": "fictional"}
    nested = b"[" * 2000 + b"0" + b"]" * 2000
    token = "eyJhbGciOiJub25lIn0." + b64url(nested) + "."
    previous_limit = sys.getrecursionlimit()
    try:
        # Freeze a bounded parser depth; pytest may otherwise raise the process limit.
        sys.setrecursionlimit(600)
        with pytest.raises(jwt.DecodeError):
            jwt.decode(token, options={"verify_signature": False})
    finally:
        sys.setrecursionlimit(previous_limit)


@pytest.mark.parametrize("curve,key_type", [
    ("Ed25519", ed25519.Ed25519PrivateKey), ("Ed448", ed448.Ed448PrivateKey),
])
def test_okp_private_public_key_consistency(curve, key_type):
    first, second = key_type.generate(), key_type.generate()
    public = first.public_key().public_bytes_raw()
    private = first.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    other = second.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    key = {"kty": "OKP", "crv": curve, "x": b64url(public), "d": b64url(private)}
    assert jwt.PyJWK.from_dict(key, algorithm="EdDSA").key.public_key().public_bytes_raw() == public
    with pytest.raises(jwt.InvalidKeyError, match="does not match"):
        jwt.PyJWK.from_dict(key | {"d": b64url(other)}, algorithm="EdDSA")


class WireSocket:
    """Own inert wire bytes; no network or arbitrary server is contacted."""

    def __init__(self, body):
        self.body = io.BytesIO(body)

    def makefile(self, *_args, **_kwargs):
        return self.body


@pytest.mark.parametrize("method", ["stream", "read_chunked"])
def test_streaming_chunk_size_line_is_bounded(method):
    wire = HTTPResponse(WireSocket(
        b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n" + b"1" * 65537
    ))
    wire.begin()
    response = urllib3.HTTPResponse(body=wire, headers=list(wire.headers.items()),
                                    preload_content=False)
    with pytest.raises(ProtocolError, match="maximum allowed length"):
        list(getattr(response, method)())
    assert response.closed


def test_deflate_tail_after_eof_does_not_remain_pending():
    decoder = DeflateDecoder()
    assert decoder.decompress(zlib.compress(b"fictional") + b"tail") == b"fictional"
    assert decoder.decompress(b"tail") == b""
    assert not decoder.has_unconsumed_tail


def test_proxy_and_origin_tls_policies_stay_distinct():
    proxy, origin = ssl.create_default_context(), ssl.create_default_context()
    manager = urllib3.ProxyManager("https://proxy.invalid", proxy_ssl_context=proxy,
                                   ssl_context=origin, use_forwarding_for_https=True)
    assert manager.proxy_config.ssl_context is proxy
    assert manager.connection_pool_kw["ssl_context"] is origin
