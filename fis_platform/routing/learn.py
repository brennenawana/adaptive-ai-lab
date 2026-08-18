"""Stdlib learners for the R5 router: logistic regression, CART, metrics, CV, digests.

Why hand-rolled rather than scikit-learn: the contract fixes the stack at the standard
library — § 9 "the routers are stdlib with JSON artifacts and stable digests" — because
the router artifact is *committed evidence* (§ 13). A committed artifact has to be
re-derivable from its JSON on any machine, years later, without a pinned BLAS deciding
the last two digits of a coefficient. So everything here is deterministic given its
inputs: no RNG, no set iteration, no dependence on dict insertion order, and every tie
broken by an explicit stated rule rather than by whatever the sort happened to do.

Two scale choices are deliberate, because they change what the hyperparameters mean:

* The logistic objective is a **sum** over samples, not a mean, and the L2 penalty is
  `l2/2 * ||w||^2` on the weights only (the intercept is unpenalized, § 9). `l2` is
  therefore denominated in samples: λ = 100 says "this weight needs about a hundred
  samples' worth of evidence". The contract's λ ∈ {0.1, 1, 10, 100} grid is read that
  way, and the same grid on a mean-scaled loss would mean something else entirely.
* Standardization is a separate object, not something `fit` does for you, because the
  CV loop must fit it *per fold* (§ 10 "fit standardizer per fold"). A model that
  standardized internally would fold test-fold means and stds into every training fit —
  a leak that shows up as an out-of-fold number that is quietly too good.

Everything is list-of-lists; there is no array type to get wrong.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any

# A column whose spread is below this is treated as constant: dividing by it would
# amplify float noise into a feature. § 9 already promises such columns carry zero
# weight ("features constant on that subset carry zero weight by construction"), and
# std = 1.0 with a zero-centred column delivers exactly that.
_CONST_STD_EPS = 1e-12

# Newton's Hessian can go singular when every fitted probability saturates (p(1-p)
# underflows to 0). This ridge is far below any real curvature and only keeps the
# elimination from dividing by zero.
_HESSIAN_RIDGE = 1e-9

# Logit clamp for the sigmoid. exp(-35) is ~6e-16, i.e. the probability is already 1
# to within double precision, so clamping changes no number a caller can observe while
# removing the overflow branch entirely.
_LOGIT_CLAMP = 35.0

# Ties in a split's impurity decrease are decided by (feature index, threshold), but
# two arithmetically identical decreases can differ in the last bit depending on the
# order the sums accumulated. Treating differences below this as ties makes the stated
# tie-break rule actually reachable instead of theoretical.
_SPLIT_TIE_EPS = 1e-12


# --------------------------------------------------------------------------- helpers


def _sigmoid(z: float) -> float:
    """Sigmoid with the logit clamped to ±35 (see `_LOGIT_CLAMP`)."""
    if z > _LOGIT_CLAMP:
        z = _LOGIT_CLAMP
    elif z < -_LOGIT_CLAMP:
        z = -_LOGIT_CLAMP
    if z >= 0.0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def _check_xy(X: list[list[float]], y: list[int]) -> tuple[int, int]:
    """Validate a design matrix / label pair and return (n_rows, n_features)."""
    n = len(X)
    if n == 0:
        raise ValueError("fit needs at least one row")
    if len(y) != n:
        raise ValueError(f"X has {n} rows but y has {len(y)}")
    d = len(X[0])
    if d == 0:
        raise ValueError("fit needs at least one feature column")
    for i, row in enumerate(X):
        if len(row) != d:
            raise ValueError(f"row {i} has {len(row)} columns, expected {d}")
    for i, label in enumerate(y):
        if label not in (0, 1):
            raise ValueError(f"y[{i}] = {label!r}; labels must be 0 or 1")
    return n, d


def solve_linear(A: list[list[float]], b: list[float]) -> list[float]:
    """Solve `A x = b` by Gaussian elimination with partial pivoting.

    Written out rather than imported because the whole point of the stdlib constraint
    is that the artifact's numbers can be reproduced from source. Partial pivoting (not
    plain elimination) because the Newton system's diagonal can be tiny for a feature
    with almost no curvature, and pivoting on it would blow up the back-substitution.
    """
    n = len(A)
    if n == 0:
        return []
    if len(b) != n:
        raise ValueError(f"A is {n}x{n} but b has {len(b)} entries")
    m = [list(row) + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) == 0.0:
            raise ValueError(f"singular matrix at column {col}")
        if pivot != col:
            m[col], m[pivot] = m[pivot], m[col]
        inv = 1.0 / m[col][col]
        for r in range(col + 1, n):
            factor = m[r][col] * inv
            if factor == 0.0:
                continue
            for c in range(col, n + 1):
                m[r][c] -= factor * m[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        acc = m[r][n]
        for c in range(r + 1, n):
            acc -= m[r][c] * x[c]
        x[r] = acc / m[r][r]
    return x


# -------------------------------------------------------------------- canonical JSON


def _canonical(obj: Any) -> Any:
    """Recursively normalize floats so two equal artifacts serialize byte-identically."""
    if obj is None or isinstance(obj, (str, bool)):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        if not math.isfinite(obj):
            # A non-finite number in an artifact means the fit broke; emitting
            # `NaN` would produce a digest over invalid JSON and hide that.
            raise ValueError(f"non-finite float in artifact: {obj!r}")
        r = round(obj, 12)
        return 0.0 if r == 0.0 else r  # -0.0 and 0.0 must not digest differently
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if not isinstance(k, str):
                raise TypeError(f"artifact dict keys must be strings, got {type(k).__name__}")
            out[k] = _canonical(v)
        return out
    if isinstance(obj, (list, tuple)):
        return [_canonical(v) for v in obj]
    raise TypeError(f"cannot canonicalize {type(obj).__name__}")


def canonical_json(obj: Any) -> str:
    """Canonical JSON: sorted keys, no whitespace, floats rounded to 12 decimals.

    12 decimals is below any difference a routing decision can see and above the
    accumulation noise that makes two mathematically identical fits differ in the last
    bit, so the digest tracks the model and not the summation order.
    """
    return json.dumps(_canonical(obj), sort_keys=True, separators=(",", ":"))


def digest(obj: Any) -> str:
    """sha256 of `canonical_json(obj)` — the `artifact_digest` of § 13."""
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


# -------------------------------------------------------------------- standardizer


class Standardizer:
    """Per-column mean / population-std scaling, fitted separately from the model.

    Population std (divide by n, not n-1): the fold *is* the population being centred,
    and the n-1 correction would make the transform depend on fold size, which the
    per-fold refit in § 10 would then bake into the out-of-fold numbers.
    """

    def __init__(self) -> None:
        self.means: list[float] = []
        self.stds: list[float] = []
        self.constant: list[bool] = []

    def fit(self, X: list[list[float]]) -> Standardizer:
        """Fit and return self — use as `Standardizer().fit(X)`."""
        n = len(X)
        if n == 0:
            raise ValueError("Standardizer.fit needs at least one row")
        d = len(X[0])
        for i, row in enumerate(X):
            if len(row) != d:
                raise ValueError(f"row {i} has {len(row)} columns, expected {d}")
        self.means = [0.0] * d
        self.stds = [1.0] * d
        self.constant = [False] * d
        for j in range(d):
            col = [float(row[j]) for row in X]
            mean = math.fsum(col) / n
            var = math.fsum((v - mean) * (v - mean) for v in col) / n
            std = math.sqrt(var) if var > 0.0 else 0.0
            self.means[j] = mean
            if std < _CONST_STD_EPS:
                self.stds[j] = 1.0
                self.constant[j] = True
            else:
                self.stds[j] = std
        return self

    def transform(self, X: list[list[float]]) -> list[list[float]]:
        d = len(self.means)
        out = []
        for i, row in enumerate(X):
            if len(row) != d:
                raise ValueError(f"row {i} has {len(row)} columns, expected {d}")
            out.append([(float(row[j]) - self.means[j]) / self.stds[j] for j in range(d)])
        return out

    def fit_transform(self, X: list[list[float]]) -> list[list[float]]:
        return self.fit(X).transform(X)

    def to_dict(self) -> dict[str, Any]:
        return {
            "means": list(self.means),
            "stds": list(self.stds),
            "constant": list(self.constant),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Standardizer:
        s = cls()
        s.means = [float(v) for v in d["means"]]
        s.stds = [float(v) for v in d["stds"]]
        s.constant = [bool(v) for v in d["constant"]]
        if not (len(s.means) == len(s.stds) == len(s.constant)):
            raise ValueError("standardizer arrays have different lengths")
        return s


# ------------------------------------------------------------- logistic regression


class LogisticRegression:
    """L2-penalized logistic regression fitted by Newton-Raphson (IRLS).

    Newton rather than gradient descent because the problem is tiny (tens of features,
    ~a hundred rows) and Newton has no learning rate to tune — one fewer thing that
    could differ between the run that produced the artifact and the run that checks it.

    `fit` expects X to be **already standardized**; see the module docstring for why.
    """

    def __init__(self, l2: float = 1.0, max_iter: int = 100, tol: float = 1e-8) -> None:
        if l2 < 0.0:
            raise ValueError("l2 must be >= 0")
        self.l2 = float(l2)
        self.max_iter = int(max_iter)
        self.tol = float(tol)
        self.intercept: float = 0.0
        self.coef: list[float] = []
        self.n_iter: int = 0
        self.converged: bool = False

    # -- objective -----------------------------------------------------------

    def _penalized_loss(self, X: list[list[float]], y: list[int], beta: list[float]) -> float:
        """Penalized negative log-likelihood, summed over samples.

        `log(1+exp(z))` is evaluated as `max(z,0) + log1p(exp(-|z|))` so a saturated
        logit costs precision, not an overflow.
        """
        terms = []
        for row, label in zip(X, y, strict=True):
            z = beta[0] + math.fsum(beta[j + 1] * row[j] for j in range(len(row)))
            terms.append(max(z, 0.0) + math.log1p(math.exp(-abs(z))) - label * z)
        total = math.fsum(terms)
        if self.l2 > 0.0:
            total += 0.5 * self.l2 * math.fsum(w * w for w in beta[1:])
        return total

    # -- fit -----------------------------------------------------------------

    def fit(self, X: list[list[float]], y: list[int]) -> LogisticRegression:
        n, d = _check_xy(X, y)
        beta = [0.0] * (d + 1)
        loss = self._penalized_loss(X, y, beta)
        self.n_iter = 0
        self.converged = False

        for it in range(1, self.max_iter + 1):
            probs = []
            for row in X:
                z = beta[0] + math.fsum(beta[j + 1] * row[j] for j in range(d))
                probs.append(_sigmoid(z))

            grad = [0.0] * (d + 1)
            grad[0] = math.fsum(probs[i] - y[i] for i in range(n))
            for j in range(d):
                grad[j + 1] = math.fsum((probs[i] - y[i]) * X[i][j] for i in range(n))
                grad[j + 1] += self.l2 * beta[j + 1]

            weights = [p * (1.0 - p) for p in probs]
            hess = [[0.0] * (d + 1) for _ in range(d + 1)]
            for i in range(n):
                w = weights[i]
                if w == 0.0:
                    continue
                row = X[i]
                # Design row with the implicit intercept column of ones in front.
                z_row = [1.0, *row]
                for a in range(d + 1):
                    wa = w * z_row[a]
                    if wa == 0.0:
                        continue
                    hrow = hess[a]
                    for b in range(a, d + 1):
                        hrow[b] += wa * z_row[b]
            for a in range(d + 1):
                for b in range(a + 1, d + 1):
                    hess[b][a] = hess[a][b]
            for a in range(1, d + 1):
                hess[a][a] += self.l2
            for a in range(d + 1):
                hess[a][a] += _HESSIAN_RIDGE

            delta = solve_linear(hess, [-g for g in grad])

            # Backtracking: Newton can overshoot badly on near-separable data, where
            # the unpenalized direction runs off toward infinite weights. Halving until
            # the penalized loss actually falls keeps the iteration monotone.
            step_scale = 1.0
            accepted: list[float] | None = None
            accepted_loss = loss
            for _ in range(21):  # the full step plus at most 20 halvings
                cand = [beta[k] + step_scale * delta[k] for k in range(d + 1)]
                cand_loss = self._penalized_loss(X, y, cand)
                if cand_loss < loss:
                    accepted = cand
                    accepted_loss = cand_loss
                    break
                step_scale *= 0.5
            if accepted is None:
                # No improving step exists at this precision: we are at the optimum as
                # far as double arithmetic can tell. That is convergence, not failure.
                self.converged = True
                break

            max_step = max(abs(step_scale * delta[k]) for k in range(d + 1))
            beta = accepted
            loss = accepted_loss
            self.n_iter = it
            if max_step < self.tol:
                self.converged = True
                break

        self.intercept = beta[0]
        self.coef = beta[1:]
        return self

    # -- use -----------------------------------------------------------------

    def decision_function(self, X: list[list[float]]) -> list[float]:
        d = len(self.coef)
        out = []
        for i, row in enumerate(X):
            if len(row) != d:
                raise ValueError(f"row {i} has {len(row)} columns, expected {d}")
            out.append(self.intercept + math.fsum(self.coef[j] * float(row[j]) for j in range(d)))
        return out

    def predict_proba(self, X: list[list[float]]) -> list[float]:
        return [_sigmoid(z) for z in self.decision_function(X)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "logistic",
            "l2": self.l2,
            "max_iter": self.max_iter,
            "tol": self.tol,
            "intercept": self.intercept,
            "coef": list(self.coef),
            "n_iter": self.n_iter,
            "converged": self.converged,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LogisticRegression:
        m = cls(l2=float(d["l2"]), max_iter=int(d["max_iter"]), tol=float(d["tol"]))
        m.intercept = float(d["intercept"])
        m.coef = [float(v) for v in d["coef"]]
        m.n_iter = int(d.get("n_iter", 0))
        m.converged = bool(d.get("converged", False))
        return m


# ------------------------------------------------------------------ decision tree


class DecisionTree:
    """CART for binary classification: Gini splits, Laplace leaf probabilities.

    Depth 2-3 with a min-leaf floor is the whole point (§ 9): a router that a reviewer
    can read as four or eight if-statements, whose every leaf is backed by at least
    `min_samples_leaf` real cases. Leaf probabilities are Laplace-smoothed,
    `(pos + 1) / (n + 2)`, so an 8-case pure leaf reports 0.9 rather than a certainty
    it has not earned — which matters because the threshold grid (§ 10) runs to 0.80.

    Split rule at predict time is `x <= threshold` goes left. Thresholds are midpoints
    between consecutive distinct training values, so the rule reproduces the training
    partition exactly.

    A split is kept whenever both children hold at least `min_samples_leaf` rows, even
    if its impurity decrease is zero — the contract's stopping rule is "depth reached,
    node pure, or no valid split" and nothing else. That is not a detail: on XOR-shaped
    data every first split has zero decrease, and a positive-decrease requirement would
    make the tree structurally unable to represent an interaction.
    """

    def __init__(self, max_depth: int = 3, min_samples_leaf: int = 8) -> None:
        if max_depth < 0:
            raise ValueError("max_depth must be >= 0")
        if min_samples_leaf < 1:
            raise ValueError("min_samples_leaf must be >= 1")
        self.max_depth = int(max_depth)
        self.min_samples_leaf = int(min_samples_leaf)
        self.n_features: int = 0
        self.tree_: dict[str, Any] | None = None

    # -- fit -----------------------------------------------------------------

    @staticmethod
    def _gini(n: int, pos: int) -> float:
        if n == 0:
            return 0.0
        p = pos / n
        return 1.0 - (p * p + (1.0 - p) * (1.0 - p))

    def _leaf(self, idx: list[int], y: list[int]) -> dict[str, Any]:
        n = len(idx)
        pos = sum(y[i] for i in idx)
        return {
            "leaf": True,
            "n": n,
            "pos": pos,
            "p": (pos + 1) / (n + 2),
        }

    def _best_split(
        self, idx: list[int], X: list[list[float]], y: list[int]
    ) -> tuple[int, float, float] | None:
        """Best (feature, threshold, impurity_decrease), or None if no split is valid.

        Features are scanned in ascending index and thresholds in ascending value, and
        a candidate replaces the incumbent only if it beats it by more than
        `_SPLIT_TIE_EPS`. That is exactly the stated tie-break: lower feature index,
        then lower threshold.
        """
        n = len(idx)
        total_pos = sum(y[i] for i in idx)
        parent = self._gini(n, total_pos)
        best: tuple[int, float, float] | None = None
        for j in range(self.n_features):
            order = sorted(idx, key=lambda i: X[i][j])
            n_left = 0
            pos_left = 0
            for k in range(n - 1):
                i = order[k]
                n_left += 1
                pos_left += y[i]
                v = X[i][j]
                v_next = X[order[k + 1]][j]
                if v == v_next:
                    continue
                n_right = n - n_left
                if n_left < self.min_samples_leaf or n_right < self.min_samples_leaf:
                    continue
                thr = (v + v_next) / 2.0
                if not (v <= thr < v_next):
                    # The midpoint rounded onto the upper value (adjacent floats):
                    # fall back to the lower value, which splits at the same boundary
                    # under the `<=` rule.
                    thr = v
                pos_right = total_pos - pos_left
                child = (
                    n_left * self._gini(n_left, pos_left)
                    + n_right * self._gini(n_right, pos_right)
                ) / n
                decrease = parent - child
                if best is None or decrease > best[2] + _SPLIT_TIE_EPS:
                    best = (j, thr, decrease)
        return best

    def _build(self, idx: list[int], X: list[list[float]], y: list[int], depth: int) -> dict:
        n = len(idx)
        pos = sum(y[i] for i in idx)
        if depth >= self.max_depth or pos == 0 or pos == n or n < 2 * self.min_samples_leaf:
            return self._leaf(idx, y)
        split = self._best_split(idx, X, y)
        if split is None:
            return self._leaf(idx, y)
        j, thr, decrease = split
        left = [i for i in idx if X[i][j] <= thr]
        right = [i for i in idx if X[i][j] > thr]
        if len(left) < self.min_samples_leaf or len(right) < self.min_samples_leaf:
            return self._leaf(idx, y)  # defensive: the sweep and the rule must agree
        return {
            "leaf": False,
            "feature": j,
            "threshold": thr,
            "n": n,
            "pos": pos,
            "decrease": decrease,
            "left": self._build(left, X, y, depth + 1),
            "right": self._build(right, X, y, depth + 1),
        }

    def fit(self, X: list[list[float]], y: list[int]) -> DecisionTree:
        """Fit on **raw** (unstandardized) X — thresholds are readable that way."""
        n, d = _check_xy(X, y)
        self.n_features = d
        self.tree_ = self._build(list(range(n)), X, y, 0)
        return self

    # -- use -----------------------------------------------------------------

    def predict_proba(self, X: list[list[float]]) -> list[float]:
        if self.tree_ is None:
            raise ValueError("tree is not fitted")
        out = []
        for i, row in enumerate(X):
            if len(row) != self.n_features:
                raise ValueError(f"row {i} has {len(row)} columns, expected {self.n_features}")
            node = self.tree_
            while not node["leaf"]:
                goes_left = float(row[node["feature"]]) <= node["threshold"]
                node = node["left"] if goes_left else node["right"]
            out.append(float(node["p"]))
        return out

    def feature_importances(self) -> list[float]:
        """Weighted impurity decrease per feature, normalized to sum to 1.

        Returns all zeros when no split carries any decrease (a tree can be built
        entirely from zero-decrease splits, e.g. the root of an XOR); normalizing that
        would invent an attribution that the fit does not support.
        """
        if self.tree_ is None:
            raise ValueError("tree is not fitted")
        totals = [0.0] * self.n_features
        root_n = self.tree_["n"]

        def walk(node: dict) -> None:
            if node["leaf"]:
                return
            totals[node["feature"]] += (node["n"] / root_n) * node["decrease"]
            walk(node["left"])
            walk(node["right"])

        walk(self.tree_)
        s = math.fsum(totals)
        if s <= 0.0:
            return [0.0] * self.n_features
        return [t / s for t in totals]

    def describe(self, feature_names: list[str]) -> str:
        """Indented if/else rendering — the artifact's human-readable face."""
        if self.tree_ is None:
            raise ValueError("tree is not fitted")
        if len(feature_names) != self.n_features:
            raise ValueError(
                f"{len(feature_names)} feature names for {self.n_features} features"
            )
        lines: list[str] = []

        def walk(node: dict, depth: int) -> None:
            pad = "  " * depth
            if node["leaf"]:
                lines.append(
                    f"{pad}leaf: p={node['p']:.4f}  n={node['n']}  pos={node['pos']}"
                )
                return
            name = feature_names[node["feature"]]
            lines.append(f"{pad}if {name} <= {node['threshold']:.6g}:  # n={node['n']}")
            walk(node["left"], depth + 1)
            lines.append(f"{pad}else:  # {name} > {node['threshold']:.6g}")
            walk(node["right"], depth + 1)

        walk(self.tree_, 0)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "tree",
            "max_depth": self.max_depth,
            "min_samples_leaf": self.min_samples_leaf,
            "n_features": self.n_features,
            "tree": copy.deepcopy(self.tree_),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DecisionTree:
        t = cls(max_depth=int(d["max_depth"]), min_samples_leaf=int(d["min_samples_leaf"]))
        t.n_features = int(d["n_features"])
        t.tree_ = copy.deepcopy(d["tree"])
        return t


# ------------------------------------------------------------------------ metrics


def roc_auc(y: list[int], p: list[float]) -> float | None:
    """ROC-AUC by the Mann-Whitney statistic with mid-ranks for ties.

    None when only one class is present: an AUC over a single class is undefined, and
    returning 0.5 there would put a meaningless number into a CV mean.
    """
    n = len(y)
    if len(p) != n:
        raise ValueError("y and p have different lengths")
    n_pos = sum(1 for v in y if v == 1)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    order = sorted(range(n), key=lambda i: p[i])
    ranks = [0.0] * n
    k = 0
    while k < n:
        j = k
        while j + 1 < n and p[order[j + 1]] == p[order[k]]:
            j += 1
        mid = (k + j) / 2.0 + 1.0  # ranks are 1-based; mid-rank over the tie block
        for t in range(k, j + 1):
            ranks[order[t]] = mid
        k = j + 1
    rank_sum = math.fsum(ranks[i] for i in range(n) if y[i] == 1)
    return (rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def average_precision(y: list[int], p: list[float]) -> float | None:
    """Average precision (PR-AUC): sum over ranked positives of precision × recall
    increment, walking the ranking from the highest score down.

    Tied scores form ONE operating point (as scikit-learn's `average_precision_score`
    does): a block of equal scores is credited at the precision reached once the whole
    block is included. The rank-wise alternative — walking a tie block in input order —
    would make the number depend on the order the cases were listed in, which for a
    shallow tree (many cases share a leaf probability) is a real bias, not a rounding
    detail. This form is order-invariant.

    None when there are no positives.
    """
    n = len(y)
    if len(p) != n:
        raise ValueError("y and p have different lengths")
    n_pos = sum(1 for v in y if v == 1)
    if n_pos == 0:
        return None
    order = sorted(range(n), key=lambda i: -p[i])
    tp = seen = 0
    total = 0.0
    i = 0
    while i < n:
        j = i
        block_pos = 0
        while j < n and p[order[j]] == p[order[i]]:
            block_pos += y[order[j]] == 1
            j += 1
        seen += j - i
        if block_pos:
            tp += block_pos
            total += (tp / seen) * (block_pos / n_pos)
        i = j
    return total


def brier(y: list[int], p: list[float]) -> float:
    """Mean squared error of the probability — the calibration half of § 10."""
    n = len(y)
    if len(p) != n:
        raise ValueError("y and p have different lengths")
    if n == 0:
        raise ValueError("brier needs at least one sample")
    return math.fsum((p[i] - y[i]) ** 2 for i in range(n)) / n


def log_loss(y: list[int], p: list[float], eps: float = 1e-15) -> float:
    """Mean negative log-likelihood, probabilities clipped into [eps, 1-eps].

    This is the model-selection criterion of § 10 (λ and depth are chosen by out-of-fold
    log-loss), so the clip matters: one saturated wrong prediction must not make a
    candidate's score infinite and therefore incomparable.
    """
    n = len(y)
    if len(p) != n:
        raise ValueError("y and p have different lengths")
    if n == 0:
        raise ValueError("log_loss needs at least one sample")
    terms = []
    for i in range(n):
        q = min(max(p[i], eps), 1.0 - eps)
        terms.append(-(math.log(q) if y[i] == 1 else math.log(1.0 - q)))
    return math.fsum(terms) / n


def confusion(y: list[int], p: list[float], threshold: float) -> dict[str, int]:
    """Counts under "predict positive iff p >= threshold" — the § 9 policy rule."""
    n = len(y)
    if len(p) != n:
        raise ValueError("y and p have different lengths")
    tp = fp = tn = fn = 0
    for i in range(n):
        predicted = p[i] >= threshold
        if y[i] == 1:
            if predicted:
                tp += 1
            else:
                fn += 1
        else:
            if predicted:
                fp += 1
            else:
                tn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


# ------------------------------------------------------------------ cross-validation


def grouped_folds(groups: list[str]) -> list[tuple[list[int], list[int]]]:
    """Leave-one-group-out folds, groups in sorted order.

    This is § 8's memorization guard: the group key is the scenario class, so a fold
    never trains on a template it is tested on. Fold order follows sorted group names
    so a CV table is diffable between runs.
    """
    uniq = sorted(set(groups))
    if len(uniq) < 2:
        raise ValueError(f"leave-one-group-out needs >= 2 groups, got {len(uniq)}")
    folds = []
    for g in uniq:
        test = [i for i, v in enumerate(groups) if v == g]
        train = [i for i, v in enumerate(groups) if v != g]
        folds.append((train, test))
    return folds


def stratified_folds(
    y: list[int], k: int, seed_order: list[int] | None = None
) -> list[tuple[list[int], list[int]]]:
    """Deterministic stratified k-fold: the i-th positive and the i-th negative go to
    fold `i % k`.

    No RNG anywhere — the "shuffle" is the traversal order, which the caller can supply
    explicitly via `seed_order` (a permutation of indices). § 8 makes this the secondary,
    exploratory CV, so it must be reproducible from the labels alone.
    """
    n = len(y)
    if k < 2:
        raise ValueError("k must be >= 2")
    if k > n:
        raise ValueError(f"k={k} exceeds n={n}")
    order = list(range(n)) if seed_order is None else list(seed_order)
    if sorted(order) != list(range(n)):
        raise ValueError("seed_order must be a permutation of range(len(y))")
    assign = [0] * n
    seen = {0: 0, 1: 0}
    for i in order:
        label = y[i]
        if label not in (0, 1):
            raise ValueError(f"y[{i}] = {label!r}; labels must be 0 or 1")
        assign[i] = seen[label] % k
        seen[label] += 1
    folds = []
    for f in range(k):
        test = [i for i in range(n) if assign[i] == f]
        train = [i for i in range(n) if assign[i] != f]
        folds.append((train, test))
    return folds


# -------------------------------------------------------------------- router model


class RouterModel:
    """Serializable router: feature order + preprocessing + classifier in one object.

    Bundled rather than left as three loose pieces because § 13 requires the artifact to
    pin the feature order together with the coefficients, and § 6/§ 13 make a mismatch
    between the artifact's order and the extractor's a fail-closed condition. Selecting
    columns *by name* here is what makes that check meaningful: a caller cannot silently
    feed the right numbers in the wrong order.
    """

    def __init__(
        self,
        family: str,
        feature_names: list[str],
        standardizer: Standardizer | None,
        model: LogisticRegression | DecisionTree,
    ) -> None:
        if family not in ("logistic", "tree"):
            raise ValueError(f"unknown family {family!r}")
        if family == "logistic" and not isinstance(model, LogisticRegression):
            raise ValueError("family 'logistic' needs a LogisticRegression")
        if family == "tree" and not isinstance(model, DecisionTree):
            raise ValueError("family 'tree' needs a DecisionTree")
        if len(set(feature_names)) != len(feature_names):
            raise ValueError("feature_names contains duplicates")
        self.family = family
        self.feature_names = list(feature_names)
        self.standardizer = standardizer
        self.model = model

    def matrix(self, features_by_name: list[dict[str, float]]) -> list[list[float]]:
        """Select the artifact's columns, in the artifact's order, by name."""
        rows = []
        for i, fv in enumerate(features_by_name):
            row = []
            for name in self.feature_names:
                if name not in fv:
                    raise KeyError(f"row {i} is missing feature {name!r}")
                row.append(float(fv[name]))
            rows.append(row)
        return rows

    def predict_proba(self, features_by_name: list[dict[str, float]]) -> list[float]:
        X = self.matrix(features_by_name)
        if self.standardizer is not None:
            X = self.standardizer.transform(X)
        return self.model.predict_proba(X)

    def coefficients(self) -> dict[str, float] | None:
        """Weights on the standardized scale, plus `__intercept__`; None for a tree."""
        if self.family != "logistic":
            return None
        model = self.model
        assert isinstance(model, LogisticRegression)
        out = {name: model.coef[j] for j, name in enumerate(self.feature_names)}
        out["__intercept__"] = model.intercept
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "feature_names": list(self.feature_names),
            "standardizer": None if self.standardizer is None else self.standardizer.to_dict(),
            "model": self.model.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RouterModel:
        family = d["family"]
        std = None if d.get("standardizer") is None else Standardizer.from_dict(d["standardizer"])
        model: LogisticRegression | DecisionTree
        if family == "logistic":
            model = LogisticRegression.from_dict(d["model"])
        elif family == "tree":
            model = DecisionTree.from_dict(d["model"])
        else:
            raise ValueError(f"unknown family {family!r}")
        return cls(family, [str(n) for n in d["feature_names"]], std, model)

    def artifact_digest(self) -> str:
        return digest(self.to_dict())
