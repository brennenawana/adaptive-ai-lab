"""Tool broker — the only path from the model to company systems.

Everything is parameterised SQL against a connection owned by the `fis_tools` role,
which has no grant on ground_truth or learning. The model cannot reach the answer key
even if a handler is wrong.

Every call is recorded as a ToolCall so the trajectory can answer "what did it
actually look at" — which is the difference between a retrieval failure and a
reasoning failure when the Discovery Controller diagnoses a bad result.
"""

from __future__ import annotations

import time
from typing import Any, Callable

import psycopg
from psycopg.rows import dict_row

from fis_platform.telemetry.clocks import dual_clock
from schemas.tool import ToolCall

from .definitions import BY_NAME

Handler = Callable[[psycopg.Connection, dict[str, Any]], Any]
HANDLERS: dict[str, Handler] = {}


def handler(name: str):
    def deco(fn: Handler) -> Handler:
        HANDLERS[name] = fn
        return fn
    return deco


def _rows(conn: psycopg.Connection, sql: str, params: tuple) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def _one(conn: psycopg.Connection, sql: str, params: tuple) -> dict | None:
    rows = _rows(conn, sql, params)
    return rows[0] if rows else None


# ------------------------------------------------------------------ handlers
@handler("get_case")
def _get_case(conn, args):
    row = _one(conn, """
        SELECT case_id, category, subject_ids, summary, status, opened_at
        FROM cases.cases WHERE case_id = %s
    """, (args["case_id"],))
    if row is None:
        raise LookupError(f"case not found: {args['case_id']}")
    return row


@handler("get_customer")
def _get_customer(conn, args):
    row = _one(conn, """
        SELECT customer_id, display_name, country, onboarding_state, created_at
        FROM customer.customers WHERE customer_id = %s
    """, (args["customer_id"],))
    if row is None:
        raise LookupError(f"customer not found: {args['customer_id']}")
    return row


@handler("get_verifications")
def _get_verifications(conn, args):
    """This customer's verifications, optionally widened to a vendor window.

    The widened form exists because `provider_outage` is DEFINED by clustering —
    "the identity vendor is timing out across many customers". With a customer-keyed
    tool only, that cluster is invisible, so the class was not hard but impossible:
    it scored 0% root-cause accuracy and was capped at 0.333 evidence recall before
    any model saw it.

    The window is anchored on this customer's own verification times rather than an
    absolute range, so the caller does not have to know when the incident was. Each
    scenario occupies its own slot on the timeline (`scenario_epoch`), which is what
    keeps a 2-hour window from returning the entire corpus.
    """
    cid = args["customer_id"]
    own = _rows(conn, """
        SELECT verification_id, provider_ref, customer_id, vendor, check_type, status,
               reason_code, event_time
        FROM identity.verifications
        WHERE customer_id = %s ORDER BY event_time
    """, (cid,))

    vendor = args.get("vendor")
    if not vendor:
        return own

    hours = int(args.get("window_hours") or 2)
    nearby = _rows(conn, """
        WITH anchor AS (
            SELECT min(event_time) AS lo, max(event_time) AS hi
            FROM identity.verifications WHERE customer_id = %s
        )
        SELECT v.verification_id, v.provider_ref, v.customer_id, v.vendor, v.check_type,
               v.status, v.reason_code, v.event_time
        FROM identity.verifications v, anchor a
        WHERE v.vendor = %s
          AND v.customer_id <> %s
          AND v.event_time BETWEEN a.lo - make_interval(hours => %s)
                               AND a.hi + make_interval(hours => %s)
        ORDER BY v.event_time
        LIMIT 50
    """, (cid, vendor, cid, hours, hours))

    return own + nearby


@handler("get_processor_activity")
def _get_processor_activity(conn, args):
    """Accepts card_id OR customer_id.

    A case often names only the customer, and requiring the caller to already know
    the card id would make some evidence unreachable — which measures the harness,
    not the model.
    """
    if cid := args.get("card_id"):
        cards = _rows(conn, """
            SELECT card_id, provider_ref, customer_id, account_id, status, issued_at
            FROM processor.cards WHERE card_id = %s
        """, (cid,))
    elif cust := args.get("customer_id"):
        cards = _rows(conn, """
            SELECT card_id, provider_ref, customer_id, account_id, status, issued_at
            FROM processor.cards WHERE customer_id = %s
        """, (cust,))
    else:
        raise ValueError("get_processor_activity requires card_id or customer_id")

    card_ids = [c["card_id"] for c in cards] or ["__none__"]
    auths = _rows(conn, """
        SELECT auth_id, provider_ref, card_id, amount, currency, merchant, mcc,
               processor_state, decline_code, authorized_at, reversed_at
        FROM processor.authorizations
        WHERE card_id = ANY(%s) ORDER BY authorized_at
    """, (card_ids,))
    setts = _rows(conn, """
        SELECT s.settlement_id, s.provider_ref, s.auth_id, s.amount, s.currency, s.settled_at
        FROM processor.settlements s
        JOIN processor.authorizations a ON a.auth_id = s.auth_id
        WHERE a.card_id = ANY(%s) ORDER BY s.settled_at
    """, (card_ids,))
    return {"cards": cards, "authorizations": auths, "settlements": setts}


@handler("get_ledger_entries")
def _get_ledger_entries(conn, args):
    """Accepts account_id OR customer_id — same reachability reason as above."""
    if acct := args.get("account_id"):
        accounts = _rows(conn, """
            SELECT account_id, customer_id, status, currency, available_balance,
                   ledger_balance, opened_at
            FROM ledger.accounts WHERE account_id = %s
        """, (acct,))
        if not accounts:
            raise LookupError(f"account not found: {acct}")
    elif cust := args.get("customer_id"):
        accounts = _rows(conn, """
            SELECT account_id, customer_id, status, currency, available_balance,
                   ledger_balance, opened_at
            FROM ledger.accounts WHERE customer_id = %s
        """, (cust,))
    else:
        raise ValueError("get_ledger_entries requires account_id or customer_id")

    # posting_seq is returned, and is the sort key.
    #
    # It is the order the postings were actually made. `posted_at` is when the event
    # OCCURRED, which the ledger consumer stamps deliberately. For almost every
    # scenario the two agree and this changes nothing.
    #
    # For S07 they disagree, and that disagreement IS the case: a reversal posted
    # before the settlement it reverses, because the settlement was delayed in
    # delivery. Reading the account in insertion order shows a credit then a debit —
    # exactly the customer's "refunded transaction was charged again". Sorting by
    # `posted_at` and hiding `posting_seq` presented a ledger that was perfectly
    # chronological and net zero, so the only correct reading of the evidence was
    # that nothing was wrong. The hazard existed in the database and was invisible
    # to every tool, which made `reversal_race` unreachable by correct reasoning and
    # rewarded guessing from the case summary instead.
    ids = [a["account_id"] for a in accounts] or ["__none__"]
    entries = _rows(conn, """
        SELECT entry_id, account_id, direction, amount, currency, reference_type,
               reference_id, posted_at, posting_seq
        FROM ledger.entries
        WHERE account_id = ANY(%s) ORDER BY posting_seq LIMIT %s
    """, (ids, int(args.get("limit", 200))))
    return {"accounts": accounts, "entries": entries}


@handler("get_risk_alerts")
def _get_risk_alerts(conn, args):
    return _rows(conn, """
        SELECT alert_id, transaction_id, rule_code, severity, status, raised_at
        FROM risk.alerts WHERE customer_id = %s ORDER BY raised_at
    """, (args["customer_id"],))


@handler("get_webhook_history")
def _get_webhook_history(conn, args):
    pev = args["provider_event_id"]
    deliveries = _rows(conn, """
        SELECT delivery_id, provider_event_id, event_type, payload_hash,
               idempotency_key, attempt, status, received_at
        FROM webhook.deliveries WHERE provider_event_id = %s ORDER BY attempt
    """, (pev,))
    events = _rows(conn, """
        SELECT event_id, provider_event_id, delivery_id, normalized_type,
               mapping_version, raw_payload, normalized_state, created_at
        FROM integration.events WHERE provider_event_id = %s ORDER BY created_at
    """, (pev,))
    return {"deliveries": deliveries, "normalized_events": events}


@handler("search_runbooks")
def _search_runbooks(conn, args):
    # Keyword search for now. pgvector is provisioned and the column exists; moving
    # to embeddings is E3, and doing it before E2 has a baseline would confound the
    # "does explicit company knowledge help" question the experiment is meant to answer.
    q = f"%{args['query'].strip()}%"
    cat = args.get("category")
    if cat:
        return _rows(conn, """
            SELECT document_id, version, doc_type, title, body
            FROM knowledge.documents
            WHERE (title ILIKE %s OR body ILIKE %s) AND %s = ANY(categories)
            LIMIT 5
        """, (q, q, cat))
    return _rows(conn, """
        SELECT document_id, version, doc_type, title, body
        FROM knowledge.documents
        WHERE title ILIKE %s OR body ILIKE %s LIMIT 5
    """, (q, q))


# -------------------------------------------------------------------- broker
class ToolBroker:
    def __init__(self, dsn: str, *, on_event: Callable[..., Any] | None = None) -> None:
        """`on_event`, keyword-only and optional, is a telemetry hook (M-STAT; NEXT_STEP_M0.md
        §6-D "TOOLS spans"): every existing caller (`ToolBroker(dsn)`) keeps working unchanged.
        When set, `invoke()` calls it as `on_event(event_name, **fields)` around every call,
        `tool_call_start` then `tool_call_end` — including the denied/unknown-tool path, since
        that is still a call the trajectory needs a span for. A raising `on_event` must never
        break a tool call: failures are swallowed in `_emit`, telemetry-only by design.
        """
        self.dsn = dsn
        self._conn: psycopg.Connection | None = None
        self.calls: list[ToolCall] = []
        self.on_event = on_event

    def __enter__(self) -> "ToolBroker":
        self._conn = psycopg.connect(self.dsn)
        return self

    def __exit__(self, *exc) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _emit(self, event: str, **fields: Any) -> None:
        """Best-effort telemetry emission. Wrapped so a broken `on_event` (wrong
        signature, a raising sink) degrades to "no telemetry for this call", never
        to a tool call failing for a reason that has nothing to do with the tool."""
        if self.on_event is None:
            return
        try:
            self.on_event(event, **fields)
        except Exception:  # noqa: BLE001 — telemetry only, never breaks a tool call
            pass

    def invoke(self, name: str, args: dict[str, Any]) -> tuple[Any, ToolCall]:
        started = time.perf_counter()
        seq = len(self.calls)
        dc_start = dual_clock()
        self._emit("tool_call_start", tool=name, sequence=seq, **dc_start)

        if name not in BY_NAME:
            call = ToolCall(tool=name, version=0, args_hash=_hash(args), status="denied",
                            error_code="unknown_tool",
                            latency_ms=int((time.perf_counter() - started) * 1000), sequence=seq,
                            ts_realtime=dc_start["ts_realtime"], ts_monotonic=dc_start["ts_monotonic"])
            self.calls.append(call)
            self._emit("tool_call_end", tool=name, sequence=seq, status=call.status,
                       error_code=call.error_code, latency_ms=call.latency_ms, **dual_clock())
            return {"error": f"unknown tool {name!r}"}, call

        definition = BY_NAME[name]
        assert self._conn is not None, "ToolBroker must be used as a context manager"

        try:
            result = HANDLERS[name](self._conn, args)
            status, error_code = "success", None
        except LookupError as exc:
            result, status, error_code = {"error": str(exc)}, "error", "not_found"
        except (psycopg.Error, KeyError, ValueError) as exc:
            # Rollback: a failed statement poisons the transaction for later calls,
            # which would turn one bad tool call into a cascade of false failures.
            self._conn.rollback()
            result, status, error_code = {"error": f"{type(exc).__name__}: {exc}"}, "error", "query_failed"

        call = ToolCall(
            tool=name, version=definition.version, args_hash=_hash(args),
            status=status, error_code=error_code,
            result_digest=_hash(result),
            latency_ms=int((time.perf_counter() - started) * 1000), sequence=seq,
            ts_realtime=dc_start["ts_realtime"], ts_monotonic=dc_start["ts_monotonic"],
        )
        self.calls.append(call)
        self._emit("tool_call_end", tool=name, sequence=seq, status=status,
                   error_code=error_code, latency_ms=call.latency_ms, **dual_clock())
        return result, call


def _hash(payload: Any) -> str:
    import hashlib
    import json
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]
