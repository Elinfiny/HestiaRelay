"""Isolated real TLS service for judge QA; ephemeral keys never become artifacts."""

import base64
import hashlib
import ipaddress
import os
import secrets
import socket
import ssl
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta

import httpx2
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


class TLSJudge:
    def __init__(self, root):
        self.root = root
        self.database = root / "state.db"
        self.key = secrets.token_urlsafe(32)
        secret = root / "login.key"
        secret.write_text(self.key)
        secret.chmod(0o600)
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "HestiaRelay CI only")])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(private.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(UTC) - timedelta(minutes=1))
            .not_valid_after(datetime.now(UTC) + timedelta(hours=1))
            .add_extension(
                x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
                critical=False,
            )
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(private, hashes.SHA256())
        )
        self.cert = root / "tls.crt"
        self.cert.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        self.private = root / "tls.key"
        self.private.write_bytes(
            private.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        self.private.chmod(0o600)
        self.spki = base64.b64encode(
            hashlib.sha256(
                private.public_key().public_bytes(
                    serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
                )
            ).digest()
        ).decode()
        self.ssl = ssl.create_default_context(cafile=str(self.cert))
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            self.port = sock.getsockname()[1]
        self.url = f"https://127.0.0.1:{self.port}"
        self.process = None

    def start(self, database=None):
        self.database = database or self.database
        env = os.environ | {
            "HESTIA_ACCESS_MODE": "judge",
            "HESTIA_PUBLIC_ORIGIN": self.url,
            "HESTIA_LOGIN_KEY_FILE": str(self.root / "login.key"),
            "HESTIA_STATE_DB": str(self.database),
            "HESTIA_BEDROCK_MODEL_ID": "",
            "AWS_EC2_METADATA_DISABLED": "true",
        }
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "hestiarelay.server:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
                "--ssl-keyfile",
                str(self.private),
                "--ssl-certfile",
                str(self.cert),
                "--no-proxy-headers",
                "--no-access-log",
            ],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            for _ in range(100):
                try:
                    r = httpx2.get(
                        self.url + "/health", verify=self.ssl, trust_env=False, timeout=0.3
                    )
                    if r.status_code == 200:
                        return self
                except httpx2.TransportError:
                    pass
                if self.process.poll() is not None:
                    raise RuntimeError("TLS judge exited during startup")
                time.sleep(0.1)
            raise TimeoutError("TLS judge did not become ready")
        except BaseException:
            self.stop()
            raise

    def stop(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
            self.process = None

    def client(self):
        return httpx2.Client(base_url=self.url, verify=self.ssl, trust_env=False)
