"""R5 learned routing — production-observable features only.

Everything under this package inherits the import ban pinned by
`tests/test_routing_no_gold_leak.py`: no `evals.scorers`, no `schemas.scenario`, no
`scenarios.generator`, nothing `ground_truth*`. See `features.py` for why the boundary
is code rather than convention.
"""

from .features import (
    FEATURE_FAMILIES,
    FEATURE_ORDER,
    FEATURE_SCHEMA_VERSION,
    FORBIDDEN_FEATURE_NAMES,
    AnswerFields,
    RoutingFeatureSnapshot,
    is_forbidden_feature_name,
    snapshot_from,
)

__all__ = [
    "FEATURE_FAMILIES", "FEATURE_ORDER", "FEATURE_SCHEMA_VERSION",
    "FORBIDDEN_FEATURE_NAMES", "AnswerFields", "RoutingFeatureSnapshot",
    "is_forbidden_feature_name", "snapshot_from",
]
