#!/usr/bin/env python3
"""FAIL-CLOSED preflight for the Crexi baseline rig.

Design rule learned the hard way: **assert the EFFECTIVE OUTCOME, never the
environment inputs.** The first version of this gate checked that every ``R2_*``
was exported empty and printed "photo mirror inert" -- while the mirror was in
fact ENABLED, because ``Settings`` has ``env_ignore_empty=True`` (settings.py:124)
so an empty env var is treated as *unset* and ``backend/.env`` supplied
``R2_BUCKET=media`` anyway. A guard that reports SAFE beside a live hazard is the
exact defect class this project exists to eliminate.

Every check below therefore resolves the real object the product code will use.
"""
from __future__ import annotations

import os
import socket
import sys

FAILED: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "\033[32mPASS\033[0m" if ok else "\033[31mFAIL\033[0m"
    print(f"  {mark}  {label}" + (f" -- {detail}" if detail else ""))
    if not ok:
        FAILED.append(label)


def main() -> int:
    port = os.environ.get("CREXI_PG_PORT", "")
    sentinel = os.environ.get("CREXI_RIG_SENTINEL", "crexi-baseline-rig")
    arm = os.environ.get("CREXI_BASELINE_ARM", "")

    print("=== Crexi baseline preflight (outcome-asserting) ===")

    # --- 1. CWD must have no .env, or Settings inherits backend/.env ------------
    # pydantic-settings resolves env_file=".env" against the PROCESS CWD.
    # This check is only meaningful because run.sh executes the preflight from the
    # SAME cwd as the command. Running the gate in one directory and the job in
    # another is how "photo mirror: ON (R2)" slipped past a green preflight once.
    cwd_env = os.path.join(os.getcwd(), ".env")
    check("cwd has no .env adjacent", not os.path.exists(cwd_env), os.getcwd())
    check("cwd is the rig work dir", os.getcwd() == os.environ.get("CREXI_RIG_WORK"),
          f"expected {os.environ.get('CREXI_RIG_WORK')}")

    from app.config.settings import Settings
    from app.services.crexi_image_client import build_crexi_mirror

    settings = Settings()

    # --- 2. R2: assert the MIRROR OBJECT, not the env vars ---------------------
    mirror = build_crexi_mirror(settings)
    check(
        "photo mirror DISABLED (build_crexi_mirror().enabled is False)",
        mirror.enabled is False,
        # Report presence, never the value: on FAIL these are live production
        # credentials and this line may land in a log or a paste.
        f"r2_bucket={settings.r2_bucket!r} "
        f"r2_account_id={'<SET>' if settings.r2_account_id else None}",
    )

    # --- 3. DB: resolve through the PRODUCT's own resolver, both flags ---------
    sys.path.insert(0, os.path.join(os.environ["WHOLESALING_REPO"], "backend"))
    from scripts.crexi_ingest import _db_url  # the real resolution path
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    for flag in ("prod", "dev"):
        try:
            raw = _db_url(flag)
        except SystemExit:
            check(f"--db {flag} resolves", False, "resolver exited")
            continue
        u = make_url(raw)
        # Host alone proves NOTHING on this machine: an ssh tunnel listens on
        # 127.0.0.1:25432 and forwards to a REMOTE postgres. Require host+port+db.
        local_host = u.host in ("127.0.0.1", "localhost")
        right_port = str(u.port) == port
        right_db = u.database == "wholesaling"
        check(
            f"--db {flag} -> rig database",
            local_host and right_port and right_db,
            f"{u.host}:{u.port}/{u.database} (rig port {port})",
        )

    # --- 4. Sentinel: prove WHICH database, not just which address ------------
    url = _db_url("prod")
    try:
        eng = create_engine(url, future=True)
        with eng.connect() as c:
            got = c.execute(text("select marker from rig_marker")).scalar()
            inner = c.execute(text("select inet_server_port()")).scalar()
            dbname = c.execute(text("select current_database()")).scalar()
        eng.dispose()
        check("rig sentinel present (proves this is the rig DB)", got == sentinel, f"marker={got!r}")
        check("server is the container's own postgres", inner == 5432 and dbname == "wholesaling",
              f"inet_server_port={inner} db={dbname}")
    except Exception as exc:  # noqa: BLE001
        check("rig database reachable + sentinel", False, f"{type(exc).__name__}: {exc}")

    # --- 5. AI arm: assert the ROUTER's answer, not the env var ---------------
    from app.ai.router import providers_for
    from app.ai.types import AiTask

    # providers_for returns a tuple of provider ID STRINGS and takes a real AiTask.
    # KIND_EXTRACT is the route key the Crexi income ladder uses (ai/routes.py).
    from app.ai.routes import KIND_EXTRACT

    probe = AiTask(kind=KIND_EXTRACT, system="", user="")
    provs = list(providers_for(probe, settings))

    if arm == "A":
        check("Arm A: NO provider can serve extract (LLM tier structurally off)",
              provs == [], f"providers_for(extract)={provs}")
    elif arm == "B":
        check("Arm B: a provider can serve extract", provs != [], f"providers_for(extract)={provs}")
    else:
        check("CREXI_BASELINE_ARM declared (A|B)", False, f"got {arm!r}")

    # --- 5b. Crexi token: report validity, NEVER the value --------------------
    tok = os.environ.get("CREXI_TOKEN", "")
    src = os.environ.get("CREXI_TOKEN_SOURCE", "?")
    if tok and tok != "rig-replay-no-token":
        import base64
        import datetime
        import json as _json

        try:
            body = tok.split(".")[1]
            body += "=" * (-len(body) % 4)
            claims = _json.loads(base64.urlsafe_b64decode(body))
            exp = datetime.datetime.fromtimestamp(claims["exp"], datetime.UTC)
            days = (exp - datetime.datetime.now(datetime.UTC)).days
            check("crexi token unexpired", days > 0, f"expires {exp:%Y-%m-%d} ({days}d), src={src}")
            check("crexi token has Comps capability",
                  "Comps" in claims.get("capabilities", []),
                  "required by the value-route comp fetch")
        except Exception as exc:  # noqa: BLE001
            check("crexi token parses", False, type(exc).__name__)
    else:
        print(f"  \033[33mNOTE\033[0m  crexi token is the replay dummy (src={src}) "
              "-- live passes will fail; replay arms are fine")

    # --- 6. Send paths inert ---------------------------------------------------
    check("kill switch on", settings.kill_switch is True)
    check("force dry-run sends", getattr(settings, "force_dry_run_sends", False) is True)

    # --- 7. z.ai experiment routing must not reach the product's AI calls -----
    check("ANTHROPIC_BASE_URL unset", not os.environ.get("ANTHROPIC_BASE_URL"),
          os.environ.get("ANTHROPIC_BASE_URL", ""))

    # --- 8. Prove egress reachability assumptions are declared, not assumed ---
    try:
        socket.create_connection(("127.0.0.1", int(port)), timeout=3).close()
        check("rig postgres accepts TCP", True)
    except OSError as exc:
        check("rig postgres accepts TCP", False, str(exc))

    print()
    if FAILED:
        print(f"PREFLIGHT FAILED ({len(FAILED)}): " + "; ".join(FAILED), file=sys.stderr)
        return 1
    print("PREFLIGHT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
