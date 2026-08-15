"""JetStream bus.

The hard constraint this file exists to satisfy: the pipeline must be genuinely
event-driven WITHOUT making the generated corpus non-deterministic. If consumer
timing could reorder effects, the same seed would stop producing the same world and
every before/after comparison would quietly lose its meaning.

Resolution — deterministic event sourcing:

  * `publish_and_drain()` publishes, then blocks until the consumer has acknowledged
    that message. The mechanism is real (broker, streams, acks, redelivery); the
    schedule is not left to timing luck.
  * Out-of-order scenarios (S07) are produced by publishing in a deliberately
    inverted order, not by hoping the scheduler cooperates.
  * A generation run is only complete when consumer lag is zero, so a
    partially-materialised world can never be scored.

This is slower than fire-and-forget. That is the correct trade: a reproducible
corpus is worth more here than throughput.
"""

from __future__ import annotations

import asyncio
import json
from typing import Awaitable, Callable

import nats
from nats.js import JetStreamContext
from nats.js.api import ConsumerConfig, DeliverPolicy, RetentionPolicy, StreamConfig
from nats.js.errors import BadRequestError

from .envelope import DomainEvent, ProviderEvent, Subject

WEBHOOK_STREAM = "FIS_WEBHOOK"
DOMAIN_STREAM = "FIS_DOMAIN"


class EventBus:
    def __init__(self, url: str = "nats://127.0.0.1:4222") -> None:
        self.url = url
        self._nc: nats.NATS | None = None
        self._js: JetStreamContext | None = None

    async def connect(self) -> "EventBus":
        self._nc = await nats.connect(self.url)
        self._js = self._nc.jetstream()
        await self._ensure_streams()
        return self

    async def close(self) -> None:
        if self._nc is not None:
            await self._nc.drain()
            self._nc = None
            self._js = None

    async def __aenter__(self) -> "EventBus":
        return await self.connect()

    async def __aexit__(self, *exc) -> None:
        await self.close()

    @property
    def js(self) -> JetStreamContext:
        if self._js is None:
            raise RuntimeError("EventBus not connected — use `async with EventBus()`")
        return self._js

    async def _ensure_streams(self) -> None:
        """Idempotent provisioning. Safe to call on every startup."""
        for name, subjects in (
            (WEBHOOK_STREAM, [f"{Subject.WEBHOOK_RECEIVED}.>"]),
            (DOMAIN_STREAM, [f"{Subject.DOMAIN_NORMALIZED}.>"]),
        ):
            try:
                await self.js.add_stream(
                    StreamConfig(
                        name=name,
                        subjects=subjects,
                        retention=RetentionPolicy.LIMITS,
                        max_msgs=1_000_000,
                        storage="file",
                    )
                )
            except BadRequestError:
                # Already exists with a compatible config.
                pass

    # ---------------------------------------------------------------- publish
    async def publish_provider_event(self, event: ProviderEvent) -> None:
        await self.js.publish(
            Subject.webhook(event.provider),
            event.model_dump_json().encode(),
            headers={"Fis-Event-Id": str(event.envelope_id)},
        )

    async def publish_domain_event(self, event: DomainEvent) -> None:
        await self.js.publish(
            Subject.domain(event.normalized_type),
            event.model_dump_json().encode(),
            headers={"Fis-Event-Id": str(event.envelope_id)},
        )

    # ---------------------------------------------------------------- consume
    async def drain(
        self,
        *,
        stream: str,
        subject: str,
        durable: str,
        handler: Callable[[dict], Awaitable[None]],
        max_wait_s: float = 5.0,
        batch: int = 32,
    ) -> int:
        """Pull every currently-available message, handle it, ack it.

        Returns how many were processed. Pull-based rather than push: the caller
        decides when work happens, which is what makes generation reproducible.
        """
        sub = await self.js.pull_subscribe(
            subject,
            durable=durable,
            stream=stream,
            config=ConsumerConfig(deliver_policy=DeliverPolicy.ALL, ack_wait=30),
        )

        processed = 0
        while True:
            try:
                msgs = await sub.fetch(batch, timeout=max_wait_s)
            except (asyncio.TimeoutError, nats.errors.TimeoutError):
                break
            if not msgs:
                break
            for msg in msgs:
                try:
                    await handler(json.loads(msg.data.decode()))
                    await msg.ack()
                    processed += 1
                except Exception:
                    # Do NOT ack — let JetStream redeliver. Silently acking a failed
                    # handler would drop the event and produce a world that is
                    # missing effects with nothing to show for it.
                    await msg.nak()
                    raise
        return processed

    async def pending(self, stream: str, durable: str) -> int:
        """Consumer lag. Generation is only complete when this is zero."""
        try:
            info = await self.js.consumer_info(stream, durable)
            return info.num_pending
        except Exception:
            return 0
