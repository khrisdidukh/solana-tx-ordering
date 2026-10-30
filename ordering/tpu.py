"""Minimal Solana TPU QUIC sender (aioquic).

Protocol (as implemented by Agave and Firedancer TPU QUIC servers):
  * QUIC v1, ALPN "solana-tpu"
  * client presents a self-signed X.509 cert carrying an ed25519 key (the
    server reads the key to look up stake; our key is unstaked)
  * one serialized transaction per unidirectional stream, stream FIN ends it
"""
import asyncio, datetime, ssl
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration

ALPN = "solana-tpu"


def _cert():
    key = ed25519.Ed25519PrivateKey.generate()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Solana node")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=365))
            .sign(key, None))
    return cert, key


class TpuConnection:
    """One QUIC connection to one TPU address; send() preserves call order
    (streams are opened and flushed in the order transactions are given)."""

    def __init__(self, host: str, port: int, timeout: float = 3.0):
        self.host, self.port, self.timeout = host, port, timeout
        self._cm = None
        self.proto = None

    async def __aenter__(self):
        cfg = QuicConfiguration(is_client=True, alpn_protocols=[ALPN],
                                verify_mode=ssl.CERT_NONE, server_name="connect",
                                idle_timeout=10.0)
        cert, key = _cert()
        cfg.certificate, cfg.private_key = cert, key
        self._cm = connect(self.host, self.port, configuration=cfg,
                           wait_connected=True)
        self.proto = await asyncio.wait_for(self._cm.__aenter__(), self.timeout)
        return self

    async def __aexit__(self, *a):
        try:
            await asyncio.wait_for(self._cm.__aexit__(*a), 2.0)
        except Exception:
            pass

    async def send(self, wire_txs):
        q = self.proto._quic
        ids = []
        for raw in wire_txs:
            sid = q.get_next_available_stream_id(is_unidirectional=True)
            q.send_stream_data(sid, bytes(raw), end_stream=True)
            ids.append(sid)
            self.proto.transmit()          # flush each tx immediately -> send order
        return ids


async def handshake_ok(host, port, timeout=3.0):
    try:
        async with TpuConnection(host, port, timeout):
            return True
    except Exception as e:  # noqa
        return repr(e)
