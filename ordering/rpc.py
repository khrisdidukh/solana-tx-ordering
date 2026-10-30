"""Small async JSON-RPC client with polite retry on rate limits."""
import asyncio
import itertools
import time

import httpx


class RpcError(Exception):
    def __init__(self, err):
        super().__init__(str(err))
        self.err = err
        self.code = err.get("code") if isinstance(err, dict) else None


class Rpc:
    def __init__(self, url: str, timeout: float = 60.0, max_retries: int = 6):
        self.url = url
        self.client = httpx.AsyncClient(timeout=timeout, http2=False)
        self.max_retries = max_retries
        self._ids = itertools.count(1)

    async def close(self):
        await self.client.aclose()

    async def call(self, method, params=None, retry=True):
        body = {"jsonrpc": "2.0", "id": next(self._ids), "method": method,
                "params": params if params is not None else []}
        delay = 0.5
        for attempt in range(self.max_retries if retry else 1):
            try:
                r = await self.client.post(self.url, json=body)
            except (httpx.TransportError, httpx.TimeoutException):
                if not retry or attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(delay)
                delay *= 2
                continue
            if r.status_code == 429 or r.status_code >= 500:
                if not retry or attempt == self.max_retries - 1:
                    r.raise_for_status()
                await asyncio.sleep(delay)
                delay *= 2
                continue
            j = r.json()
            if "error" in j:
                raise RpcError(j["error"])
            return j["result"]
        raise RuntimeError("unreachable")

    async def send_raw(self, b64_tx: str):
        """sendTransaction exactly once (no RPC-side rebroadcast, no preflight).
        Returns (signature_or_None, error_or_None, t_request, t_response)."""
        t0 = time.time()
        try:
            sig = await self.call("sendTransaction", [b64_tx, {
                "encoding": "base64", "skipPreflight": True, "maxRetries": 0}],
                retry=False)
            return sig, None, t0, time.time()
        except Exception as e:  # noqa: BLE001 - record any failure as data
            return None, repr(e), t0, time.time()


BLOCK_OPTS = {"maxSupportedTransactionVersion": 1, "transactionDetails": "full",
              "rewards": False, "encoding": "json", "commitment": "confirmed"}
