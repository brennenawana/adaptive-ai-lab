"""NeMo Switchyard as a routing gateway — an OpenAI-compatible hop, nothing more.

Switchyard sits *beneath* the FIS gateway contract, not beside it. From the
orchestrator's point of view a routed model is one more registry entry: same
`GenerationRequest`, same `GenerationResponse`, same trajectory. What changes is
that the entry's `base_url` is the Switchyard listener and its `model_id` is a
Switchyard route id; Switchyard chooses (or, in passthrough, does not choose) the
backend and forwards the body.

Deliberately a subclass of the local llama.cpp adapter rather than a new transport:
the pivot guide's first Switchyard experiment (R1) is a *zero-semantic-change*
transport experiment, and the cleanest way to guarantee the routed arm sends the
same request as the direct arm is to build it with the same code. `build_body` is
inherited untouched; `test_switchyard_passthrough.py` asserts the two bodies are
byte-identical.

Boundary, stated once: this module records what the gateway *reported* into the
FIS `RoutingRecord`. It never reads scenario truth, never scores, never decides
whether an answer was good. If Switchyard is replaced, this file is what changes.
"""

from __future__ import annotations

from importlib import metadata as _md

import httpx

from schemas.routing import RoutingRecord

from .base import GenerationRequest, GenerationResponse
from .local import LocalLlamaCppAdapter

# Response headers Switchyard sets when a routing backend recorded a selection.
# A passthrough route records none — that is expected and is written down as
# None rather than back-filled from the profile, so the record says only what
# the gateway actually said.
_H_SELECTED_MODEL = "x-switchyard-selected-model"
_H_SELECTED_PROVIDER = "x-switchyard-selected-provider"
_H_CORRELATION_ID = "x-switchyard-router-correlation-id"


def installed_switchyard_version() -> str | None:
    try:
        return _md.version("nemo-switchyard")
    except _md.PackageNotFoundError:
        return None


class SwitchyardAdapter(LocalLlamaCppAdapter):
    """OpenAI-compatible calls through a Switchyard listener."""

    def _check_policy(self, req: GenerationRequest) -> None:
        # The base check keys on provider; a gateway's provider says nothing about
        # where the *backends* are. Use the profile's declaration instead, which
        # is deliberately conservative (True only if every backend is local).
        from schemas.common import DataPolicy

        profile = self.manifest.routing
        leaves_machine = not (profile and profile.all_backends_local)
        if req.data_policy is DataPolicy.LOCAL_ONLY and leaves_machine:
            from .base import PolicyViolation
            raise PolicyViolation(
                f"request is LOCAL_ONLY but route '{self.manifest.ref}' may reach a "
                f"non-local backend ({profile.backends if profile else 'unknown'})"
            )

    async def health(self) -> bool:
        """Listener up AND the route this entry names is registered.

        A gateway that is up but does not know the route would fail every request
        with a 404 that reads, in aggregate, exactly like a broken model.
        """
        root = self._base.removesuffix("/v1")
        try:
            async with httpx.AsyncClient(timeout=5.0) as c:
                h = await c.get(f"{root}/health")
                if h.status_code != 200 or h.json().get("status") != "ok":
                    return False
                m = await c.get(f"{self._base}/models")
                ids = {x.get("id") for x in (m.json().get("data") or [])}
                return self.manifest.model_id in ids
        except (httpx.HTTPError, ValueError):
            return False

    def _annotate(self, resp: GenerationResponse, headers: httpx.Headers) -> GenerationResponse:
        profile = self.manifest.routing
        if profile is None:  # cannot happen — the manifest validator forbids it
            return resp
        payload = resp.raw or {}
        resp.routing = RoutingRecord(
            gateway=profile.gateway,
            gateway_version=profile.gateway_version,
            route_profile=profile.route_profile,
            route_mode=profile.route_mode,
            decision_id=headers.get(_H_CORRELATION_ID),
            selected_backend=headers.get(_H_SELECTED_MODEL)
            or headers.get(_H_SELECTED_PROVIDER),
            # llama.cpp echoes the model it served (its --alias). Through the
            # gateway this is the one field Switchyard rewrites, so it is the
            # cheapest end-to-end check that the request reached the intended
            # backend and not the OpenAI default the gateway would fall back to.
            upstream_model=payload.get("model"),
        )
        return resp
