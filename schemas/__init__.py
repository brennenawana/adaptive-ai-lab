"""FIS schemas — the six foundational contracts plus the two FIS-domain ones.

Canonical Architecture, §16: before downloading a pile of models, build the task
schema, specialist schema, tool schema, trajectory schema, model gateway and
evaluation runner. These are those contracts.
"""

from .common import (
    Base,
    Confidence,
    CostRecord,
    DataPolicy,
    FrozenBase,
    LatencyRecord,
    ModelTier,
    Provider,
    RiskClass,
    TokenUsage,
    new_trace_id,
    utc_now,
)
from .investigator import Fact, InvestigationResult, NextAction, RootCause, RootCauseLabel
from .model_manifest import CliInvocation, ModelManifest, ModelRegistry, PriceTable
from .routing import GOLD_FEATURE_NAMES, RouteMode, RoutingProfile, RoutingRecord
from .scenario import CaseScore, DimensionScore, EvalRun, ScenarioManifest, SeedSplit
from .specialist import ContextPolicy, ModelBinding, RoutingPolicy, Specialist, TaskState
from .tool import ToolCall, ToolDefinition, ToolKind
from .trajectory import (
    FailureClass,
    HumanFeedback,
    ModelInvocation,
    RetrievalRef,
    RouterDecision,
    Trajectory,
    VerificationResult,
)

__all__ = [
    "Base", "FrozenBase", "Confidence", "utc_now", "new_trace_id",
    "RiskClass", "DataPolicy", "ModelTier", "Provider",
    "TokenUsage", "CostRecord", "LatencyRecord",
    "ToolDefinition", "ToolCall", "ToolKind",
    "Specialist", "TaskState", "ContextPolicy", "RoutingPolicy", "ModelBinding",
    "Trajectory", "ModelInvocation", "RouterDecision", "RetrievalRef",
    "VerificationResult", "HumanFeedback", "FailureClass",
    "ModelManifest", "ModelRegistry", "PriceTable", "CliInvocation",
    "RoutingProfile", "RoutingRecord", "RouteMode", "GOLD_FEATURE_NAMES",
    "InvestigationResult", "Fact", "RootCause", "RootCauseLabel", "NextAction",
    "ScenarioManifest", "SeedSplit", "CaseScore", "DimensionScore", "EvalRun",
]
