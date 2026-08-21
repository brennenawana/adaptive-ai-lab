"""Validate one experiment-contract spec (JSON) against `fis_platform.contract_spec`.

    python scripts/contract_check.py <path/to/spec.json>

Prints `OK <contract_spec_digest>` and exits 0 on a valid spec. Prints every
validation problem (`ContractSpecError` lists ALL of them, not just the first — see
`fis_platform/contract_spec.py`) to stderr and exits 1 otherwise. Exits 2 on a
usage error (wrong argument count) or if the file cannot be read / is not valid
JSON — those are not contract-content problems, so they are kept out of the
`ContractSpecError` list.

Read-only: no registry write, no split access, no freeze. A future R7 freeze will
require `contract_spec_digest` in the CONTRACT_FROZEN payload — the registry side
of wiring that in is a different unit; this script only exposes the digest.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.contract_spec import ContractSpecError, validate_contract_spec  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <spec.json>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        return 2
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"{path} is not valid JSON: {exc}", file=sys.stderr)
        return 2

    try:
        spec = validate_contract_spec(data)
    except ContractSpecError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"OK {spec.contract_spec_digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
