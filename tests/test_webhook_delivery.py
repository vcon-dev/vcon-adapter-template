"""Delivery tests: HMAC signature shape, retry, DLQ, conserver-direct delivery."""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from __ADAPTER_PACKAGE__.webhook_delivery import ConserverDelivery, WebhookDelivery


class _Endpoint:
    def __init__(self, url: str, secret: str = "", timeout: int = 30) -> None:
        self.url = url
        self.hmac_secret = secret
        self.timeout_seconds = timeout


def test_hmac_signature_format() -> None:
    body = b'{"vcon":"0.4.0"}'
    secret = "shh"
    sig = WebhookDelivery._sign(body, secret)
    assert sig.startswith("sha256=")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert sig == f"sha256={expected}"


@pytest.mark.asyncio
async def test_dlq_written_when_no_endpoints(tmp_path) -> None:
    wd = WebhookDelivery(endpoints=[], dead_letter_path=tmp_path)
    vcon = {"uuid": "abc-123", "vcon": "0.4.0"}
    ok = await wd.deliver(vcon)
    assert ok is False
    dlq_file = tmp_path / "abc-123.vcon.json"
    assert dlq_file.exists()
    assert json.loads(dlq_file.read_text())["uuid"] == "abc-123"


# --- ConserverDelivery ---------------------------------------------------


@pytest.mark.asyncio
async def test_conserver_delivery_posts_token_header_and_ingress_lists(tmp_path) -> None:
    """POST {base_url}/vcon with the token header and repeated `ingress_lists`
    query params, matching vcon-server's `POST /vcon` route
    (`ingress_lists: Optional[List[str]] = Query(None, ...)` in api/api.py).
    """
    received: dict = {}

    async def handler(request: web.Request) -> web.Response:
        received["headers"] = dict(request.headers)
        received["query"] = list(request.query.items())
        received["body"] = await request.json()
        return web.json_response({"ok": True}, status=201)

    app = web.Application()
    app.router.add_post("/vcon", handler)
    server = TestServer(app)
    await server.start_server()
    try:
        delivery = ConserverDelivery(
            base_url=str(server.make_url("")),
            token="tok-123",
            ingress_lists=["alpha", "beta"],
            dead_letter_path=tmp_path,
        )
        vcon = {"uuid": "abc-123", "vcon": "0.4.0"}
        ok = await delivery.deliver(vcon)
    finally:
        await server.close()

    assert ok is True
    assert received["headers"]["x-conserver-api-token"] == "tok-123"
    assert received["headers"]["Idempotency-Key"] == "abc-123"
    ingress_lists = [v for k, v in received["query"] if k == "ingress_lists"]
    assert ingress_lists == ["alpha", "beta"]
    assert received["body"]["uuid"] == "abc-123"
    assert not (tmp_path / "abc-123.vcon.json").exists()


@pytest.mark.asyncio
async def test_conserver_delivery_custom_token_header(tmp_path) -> None:
    received: dict = {}

    async def handler(request: web.Request) -> web.Response:
        received["headers"] = dict(request.headers)
        return web.json_response({"ok": True}, status=201)

    app = web.Application()
    app.router.add_post("/vcon", handler)
    server = TestServer(app)
    await server.start_server()
    try:
        delivery = ConserverDelivery(
            base_url=str(server.make_url("")),
            token="tok-456",
            token_header="x-custom-token",
            dead_letter_path=tmp_path,
        )
        ok = await delivery.deliver({"uuid": "custom-1", "vcon": "0.4.0"})
    finally:
        await server.close()

    assert ok is True
    assert received["headers"]["x-custom-token"] == "tok-456"
    assert "x-conserver-api-token" not in received["headers"]


@pytest.mark.asyncio
async def test_conserver_delivery_dlq_on_failure(tmp_path) -> None:
    async def handler(request: web.Request) -> web.Response:
        return web.Response(status=500)

    app = web.Application()
    app.router.add_post("/vcon", handler)
    server = TestServer(app)
    await server.start_server()
    try:
        delivery = ConserverDelivery(
            base_url=str(server.make_url("")),
            max_attempts=1,
            dead_letter_path=tmp_path,
        )
        ok = await delivery.deliver({"uuid": "fail-1", "vcon": "0.4.0"})
    finally:
        await server.close()

    assert ok is False
    dlq_file = tmp_path / "fail-1.vcon.json"
    assert dlq_file.exists()
    assert json.loads(dlq_file.read_text())["uuid"] == "fail-1"
