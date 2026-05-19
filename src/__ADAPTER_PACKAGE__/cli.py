"""Entry point. Wires config, source poller/listener, vCon builder, webhook delivery."""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

import structlog

from .config import load_config
from .health_server import HealthServer

log = structlog.get_logger(__name__)


async def run() -> int:
    config = load_config()

    logging.basicConfig(level=config.logging.level)
    structlog.configure(processors=[structlog.processors.JSONRenderer()])

    log.info("starting", adapter=config.adapter.name, version="0.1.0")

    health = HealthServer(host=config.server.host, port=config.server.port)
    await health.start()

    # TODO: wire your source-platform listener/poller here
    # source = MySourceClient(config.source)
    # builder = VconBuilder(config.vcon)
    # delivery = WebhookDelivery(config.webhook)
    # await source.run(lambda event: deliver(event, builder, delivery))

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    await stop.wait()
    await health.stop()
    log.info("stopped")
    return 0


def main() -> None:
    sys.exit(asyncio.run(run()))
