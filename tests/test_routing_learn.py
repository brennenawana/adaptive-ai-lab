"""The learners are only trustworthy if their arithmetic is checkable by hand.

R5 commits a router artifact as evidence (contract § 13) and then reads a routing
decision off it. So these tests do not ask "does it look like it learned" — they pin
numbers a reader can verify with a pencil: an AUC of 0.75 on four points, a Laplace leaf
of 0.9 on eight pure cases, an intercept that equals the log-odds of the base rate when
the penalty has crushed every weight. Anything vaguer would pass on a subtly wrong
implementation, which is exactly the failure mode a stdlib re-implementation has.

Determinism gets the same treatment: two fits of the same data must produce the same
digest, and the digest must survive a fresh process, because § 13 identifies an artifact
by that hash.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

from fis_platform.routing.learn import (
    DecisionTree,
    LogisticRegression,
    RouterModel,
    Standardizer,
    average_precision,
    brier,
    canonical_json,
    confusion,
    digest,
    grouped_folds,
    log_loss,
    roc_auc,
    solve_linear,
    stratified_folds,
)

ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------ standardizer


def test_standardizer_population_moments_and_constant_columns():
    # column 0: mean 2, population var ((1+0+1)/3) -> std 0.816497; column 1: constant.
    X = [[1.0, 7.0], [2.0, 7.0], [3.0, 7.0]]
    s = Standardizer().fit(X)
    assert s.means == pytest.approx([2.0, 7.0])
    assert s.stds[0] == pytest.approx(math.sqrt(2.0 / 3.0))
    assert s.stds[1] == 1.0          # constant column is not divided by ~0
    assert s.constant == [False, True]
    Z = s.transform(X)
    assert [row[1] for row in Z] == [0.0, 0.0, 0.0]   # zero weight by construction
    assert Z[0][0] == pytest.approx(-1.0 / math.sqrt(2.0 / 3.0))
    assert math.fsum(row[0] for row in Z) == pytest.approx(0.0, abs=1e-12)
    back = Standardizer.from_dict(s.to_dict())
    assert back.transform(X) == Z


# ---------------------------------------------------------- logistic regression


def test_logistic_sign_and_monotonicity():
    X = [[x] for x in (-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0)]
    y = [0, 0, 0, 0, 1, 1, 1, 1]
    m = LogisticRegression(l2=1.0).fit(X, y)
    assert m.coef[0] > 0.0
    p = m.predict_proba(X)
    assert all(p[i] < p[i + 1] for i in range(len(p) - 1))
    assert p[0] < 0.5 < p[-1]


def test_logistic_symmetric_data_has_zero_intercept():
    # Five cases at x=-1 labelled 0 and five at x=+1 labelled 1: the loss is even in
    # the intercept, so its optimum is exactly 0 and any bias in the solver shows up.
    X = [[-1.0]] * 5 + [[1.0]] * 5
    y = [0] * 5 + [1] * 5
    m = LogisticRegression(l2=1.0).fit(X, y)
    assert abs(m.intercept) < 1e-9
    assert m.coef[0] > 0.0
    assert m.predict_proba([[0.0]])[0] == pytest.approx(0.5, abs=1e-9)


def test_logistic_huge_penalty_leaves_intercept_at_the_base_rate_log_odds():
    # 3 positives out of 10. The intercept is unpenalized, so as lambda crushes the
    # weight the fit degenerates to the base-rate-only model: logit(0.3) = -0.8473.
    X = [[float(i)] for i in range(10)]
    y = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0]
    assert sum(y) == 3
    m = LogisticRegression(l2=1e6, max_iter=200).fit(X, y)
    assert abs(m.coef[0]) < 1e-4
    assert m.intercept == pytest.approx(math.log(0.3 / 0.7), abs=1e-2)

    # ... and a light penalty does not do that: the weight stays materially non-zero.
    light = LogisticRegression(l2=0.1).fit(X, y)
    assert abs(light.coef[0]) > 10 * abs(m.coef[0])


def test_logistic_newton_converges_on_two_features():
    X = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0],
         [2.0, 1.0], [1.0, 2.0], [2.0, 2.0], [0.0, 2.0]]
    y = [0, 0, 0, 1, 1, 1, 1, 0]
    m = LogisticRegression(l2=1.0).fit(X, y)
    assert m.converged is True
    assert 0 < m.n_iter <= 20          # Newton, not gradient descent
    assert len(m.coef) == 2


def test_logistic_separable_data_does_not_diverge():
    # Perfectly separable: the unpenalized direction runs to infinity, and the
    # backtracking line search is what keeps the fit finite and monotone.
    X = [[-5.0], [-4.0], [-3.0], [3.0], [4.0], [5.0]]
    y = [0, 0, 0, 1, 1, 1]
    m = LogisticRegression(l2=0.5, max_iter=100).fit(X, y)
    assert all(math.isfinite(v) for v in [m.intercept, *m.coef])
    assert m.converged is True
    assert m.predict_proba([[-5.0]])[0] < 0.05
    assert m.predict_proba([[5.0]])[0] > 0.95


def test_logistic_roundtrip_and_digest_stability():
    X = [[0.0, 1.0], [1.0, 0.0], [1.0, 1.0], [2.0, 0.5], [0.5, 2.0], [2.0, 2.0]]
    y = [0, 0, 1, 1, 0, 1]
    a = LogisticRegression(l2=1.0).fit(X, y)
    b = LogisticRegression(l2=1.0).fit(X, y)
    assert digest(a.to_dict()) == digest(b.to_dict())      # no randomness anywhere
    back = LogisticRegression.from_dict(a.to_dict())
    assert back.predict_proba(X) == a.predict_proba(X)     # exact, not approx
    assert (back.intercept, back.coef) == (a.intercept, a.coef)


def test_logistic_probability_clamp_is_finite_at_absurd_inputs():
    m = LogisticRegression()
    m.intercept = 0.0
    m.coef = [1.0]
    assert m.predict_proba([[1e9]])[0] == pytest.approx(1.0, abs=1e-12)
    assert m.predict_proba([[-1e9]])[0] == pytest.approx(0.0, abs=1e-12)


def test_solve_linear_needs_pivoting():
    # A zero leading pivot: without partial pivoting this divides by zero.
    A = [[0.0, 1.0], [1.0, 1.0]]
    x = solve_linear(A, [1.0, 3.0])
    assert x == pytest.approx([2.0, 1.0])
    with pytest.raises(ValueError):
        solve_linear([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])


# ----------------------------------------------------------------- decision tree


def _xor_data(per_cell: int = 8) -> tuple[list[list[float]], list[int]]:
    X: list[list[float]] = []
    y: list[int] = []
    for a, b, label in ((0.0, 0.0, 0), (0.0, 1.0, 1), (1.0, 0.0, 1), (1.0, 1.0, 0)):
        X.extend([[a, b]] * per_cell)
        y.extend([label] * per_cell)
    return X, y


def test_tree_learns_xor_at_depth_two_with_laplace_leaves():
    X, y = _xor_data(8)
    t = DecisionTree(max_depth=2, min_samples_leaf=8).fit(X, y)
    root = t.tree_
    assert root["feature"] == 0 and root["threshold"] == 0.5
    assert root["decrease"] == 0.0     # no single split helps on XOR; the rule allows it
    leaves = []

    def collect(node):
        if node["leaf"]:
            leaves.append(node)
            return
        collect(node["left"])
        collect(node["right"])

    collect(root)
    assert len(leaves) == 4
    assert all(leaf["n"] == 8 and leaf["pos"] in (0, 8) for leaf in leaves)
    # Laplace: (0+1)/(8+2) = 0.1 and (8+1)/(8+2) = 0.9 -- never 0 or 1.
    assert sorted({leaf["p"] for leaf in leaves}) == [0.1, 0.9]
    assert sorted(set(t.predict_proba(X))) == [0.1, 0.9]
    # Every case lands in the leaf that matches its own label.
    assert all((p > 0.5) == bool(label) for p, label in zip(t.predict_proba(X), y))


def test_tree_respects_min_samples_leaf():
    X, y = _xor_data(8)
    X, y = X[:20], y[:20]
    # 20 rows, min leaf 11: every split leaves a child of at most 9 -> no valid split.
    t = DecisionTree(max_depth=3, min_samples_leaf=11).fit(X, y)
    assert t.tree_["leaf"] is True
    assert t.tree_["n"] == 20
    assert t.feature_importances() == [0.0, 0.0]


def test_tree_depth_cap_holds():
    X, y = _xor_data(8)
    t = DecisionTree(max_depth=1, min_samples_leaf=8).fit(X, y)
    assert t.tree_["leaf"] is False
    assert t.tree_["left"]["leaf"] is True and t.tree_["right"]["leaf"] is True

    deep = DecisionTree(max_depth=3, min_samples_leaf=1).fit(X, y)

    def depth(node):
        return 0 if node["leaf"] else 1 + max(depth(node["left"]), depth(node["right"]))

    assert depth(deep.tree_) <= 3


def test_tree_tie_breaks_on_lowest_feature_then_lowest_threshold():
    # Duplicated columns: the two features are indistinguishable, so the rule must
    # pick index 0 rather than whichever the loop happened to visit last.
    values = [0.0] * 4 + [1.0] * 4 + [2.0] * 4 + [3.0] * 4
    X = [[v, v] for v in values]
    y = [0] * 4 + [1] * 4 + [0] * 4 + [1] * 4
    # Splitting at 0.5 and at 2.5 are exactly symmetric (same impurity decrease);
    # splitting at 1.5 gains nothing. The lower threshold must win.
    t = DecisionTree(max_depth=1, min_samples_leaf=4).fit(X, y)
    assert (t.tree_["feature"], t.tree_["threshold"]) == (0, 0.5)

    again = DecisionTree(max_depth=1, min_samples_leaf=4).fit(X, y)
    assert digest(again.to_dict()) == digest(t.to_dict())


def test_tree_roundtrip_and_importances():
    X, y = _xor_data(8)
    t = DecisionTree(max_depth=2, min_samples_leaf=8).fit(X, y)
    back = DecisionTree.from_dict(t.to_dict())
    assert back.predict_proba(X) == t.predict_proba(X)
    assert back.to_dict() == t.to_dict()
    assert back.feature_importances() == t.feature_importances()

    imp = t.feature_importances()
    assert math.fsum(imp) == pytest.approx(1.0)
    # On XOR the root split (feature 0) has zero decrease; all of it sits on feature 1.
    assert imp == pytest.approx([0.0, 1.0])

    text = t.describe(["f0", "f1"])
    assert text.splitlines()[0].startswith("if f0 <= 0.5")
    assert "  if f1 <= 0.5" in text          # indentation marks the second level
    assert text.count("leaf:") == 4


def test_tree_serialization_survives_a_json_round_trip():
    import json

    X, y = _xor_data(8)
    t = DecisionTree(max_depth=2, min_samples_leaf=8).fit(X, y)
    revived = DecisionTree.from_dict(json.loads(json.dumps(t.to_dict())))
    assert revived.predict_proba(X) == t.predict_proba(X)


# ----------------------------------------------------------------------- metrics


def test_roc_auc_hand_example_and_ties():
    # Ranks ascending: .1(neg) .35(pos) .4(neg) .8(pos) -> pos rank sum 6,
    # (6 - 2*3/2) / (2*2) = 0.75.
    assert roc_auc([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]) == pytest.approx(0.75)
    assert roc_auc([0, 0, 1, 1], [0.1, 0.2, 0.3, 0.4]) == pytest.approx(1.0)
    assert roc_auc([1, 1, 0, 0], [0.1, 0.2, 0.3, 0.4]) == pytest.approx(0.0)
    assert roc_auc([0, 1, 0, 1], [0.5, 0.5, 0.5, 0.5]) == pytest.approx(0.5)
    # A single tied pair is worth half a concordance, not a whole one.
    assert roc_auc([0, 1], [0.5, 0.5]) == pytest.approx(0.5)
    assert roc_auc([1, 1, 1], [0.1, 0.2, 0.3]) is None
    assert roc_auc([0, 0], [0.1, 0.2]) is None


def test_average_precision_hand_example():
    # Ranked by descending p: .8(pos, precision 1/1), .4(neg), .35(pos, 2/3), .1(neg).
    # AP = (1 + 2/3) / 2 = 0.833333...
    assert average_precision([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]) == pytest.approx(5 / 6)
    assert average_precision([0, 0, 1, 1], [0.1, 0.2, 0.3, 0.4]) == pytest.approx(1.0)
    # Everything tied: one operating point (precision 2/4 at recall 1), as sklearn —
    # and the same number whichever order the cases are listed in. A shallow tree puts
    # many cases on one leaf probability, so tie handling is a real property here.
    assert average_precision([0, 0, 1, 1], [0.5] * 4) == pytest.approx(0.5)
    assert average_precision([1, 1, 0, 0], [0.5] * 4) == pytest.approx(0.5)
    assert average_precision([0, 0, 0], [0.1, 0.2, 0.3]) is None


def test_brier_and_log_loss_numbers():
    assert brier([0, 1], [0.25, 0.75]) == pytest.approx(0.0625)
    assert brier([1, 1], [1.0, 1.0]) == 0.0
    assert log_loss([1], [0.5]) == pytest.approx(math.log(2.0))
    assert log_loss([1, 0], [0.9, 0.2]) == pytest.approx(
        (-math.log(0.9) - math.log(0.8)) / 2
    )
    # The clip keeps a confidently wrong prediction finite and therefore comparable.
    assert log_loss([1], [0.0]) == pytest.approx(-math.log(1e-15))
    assert math.isfinite(log_loss([0], [1.0]))


def test_confusion_uses_greater_or_equal():
    assert confusion([0, 1, 1, 0], [0.6, 0.7, 0.2, 0.1], 0.5) == {
        "tp": 1, "fp": 1, "tn": 1, "fn": 1
    }
    # p exactly at the threshold counts as an escalation.
    assert confusion([1, 0], [0.5, 0.5], 0.5) == {"tp": 1, "fp": 1, "tn": 0, "fn": 0}
    counts = confusion([1, 0, 1, 0], [0.9, 0.8, 0.1, 0.2], 0.85)
    assert sum(counts.values()) == 4


# ------------------------------------------------------------------------- folds


def test_grouped_folds_leave_one_class_out():
    groups = ["S03", "S01", "S02", "S01", "S03", "S03"]
    folds = grouped_folds(groups)
    assert len(folds) == 3                                  # one per distinct group
    assert [sorted(test) for _, test in folds] == [[1, 3], [2], [0, 4, 5]]  # sorted names
    seen: list[int] = []
    for train, test in folds:
        seen.extend(test)
        assert set(train) | set(test) == set(range(len(groups)))
        assert not set(train) & set(test)
        test_groups = {groups[i] for i in test}
        train_groups = {groups[i] for i in train}
        assert not test_groups & train_groups               # no group on both sides
    assert sorted(seen) == list(range(len(groups)))         # test sets partition the data
    with pytest.raises(ValueError):
        grouped_folds(["S01", "S01"])


def test_stratified_folds_partition_and_keep_balance():
    y = [1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1]                # 5 positives, 7 negatives
    folds = stratified_folds(y, 3)
    assert len(folds) == 3
    seen: list[int] = []
    pos_counts = []
    for train, test in folds:
        seen.extend(test)
        assert set(train) | set(test) == set(range(len(y)))
        assert not set(train) & set(test)
        pos_counts.append(sum(y[i] for i in test))
    assert sorted(seen) == list(range(len(y)))
    assert max(pos_counts) - min(pos_counts) <= 1           # balance within +/-1
    neg_counts = [len(test) - pc for (_, test), pc in zip(folds, pos_counts)]
    assert max(neg_counts) - min(neg_counts) <= 1

    # An explicit traversal order changes the assignment but keeps the guarantees, and
    # it is a pure function of that order -- no RNG.
    order = list(reversed(range(len(y))))
    a = stratified_folds(y, 3, seed_order=order)
    b = stratified_folds(y, 3, seed_order=order)
    assert a == b
    assert a != folds
    with pytest.raises(ValueError):
        stratified_folds(y, 3, seed_order=[0, 0, 1])


# ------------------------------------------------------- canonical json / digests


def test_canonical_json_is_order_and_noise_insensitive():
    assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})
    assert canonical_json({"a": 1.0}) == '{"a":1.0}'
    assert canonical_json({"a": -0.0}) == canonical_json({"a": 0.0})
    # Below 1e-12 the two are the same artifact; above it they are not.
    assert canonical_json([0.1 + 0.2]) == canonical_json([0.3])
    assert canonical_json([0.3]) != canonical_json([0.3 + 1e-9])
    with pytest.raises(ValueError):
        canonical_json([float("nan")])
    assert digest({"a": 1}) == digest({"a": 1})
    assert digest({"a": 1}) != digest({"a": 2})


# ------------------------------------------------------------------ router model


def _fitted_router() -> RouterModel:
    raw = [[0.0, 10.0], [1.0, 11.0], [2.0, 9.0], [3.0, 12.0], [4.0, 8.0], [5.0, 13.0]]
    y = [0, 0, 0, 1, 1, 1]
    std = Standardizer().fit(raw)
    model = LogisticRegression(l2=1.0).fit(std.transform(raw), y)
    return RouterModel("logistic", ["n_violations", "output_tokens"], std, model)


def test_router_selects_columns_by_name_not_by_dict_order():
    router = _fitted_router()
    a = router.predict_proba([{"n_violations": 4.0, "output_tokens": 8.0}])
    b = router.predict_proba([{"output_tokens": 8.0, "n_violations": 4.0}])
    assert a == b
    # Extra keys are ignored; a missing one is a hard error, not a silent zero.
    c = router.predict_proba([{"output_tokens": 8.0, "n_violations": 4.0, "junk": 99.0}])
    assert c == a
    with pytest.raises(KeyError):
        router.predict_proba([{"n_violations": 4.0}])
    # Swapping the values must change the answer -- proof the mapping is by name.
    d = router.predict_proba([{"n_violations": 8.0, "output_tokens": 4.0}])
    assert d != a


def test_router_coefficients_and_digest_sensitivity():
    router = _fitted_router()
    coefs = router.coefficients()
    assert set(coefs) == {"n_violations", "output_tokens", "__intercept__"}
    assert coefs["n_violations"] == router.model.coef[0]

    first = router.artifact_digest()
    assert first == router.artifact_digest()                 # stable within a process
    assert RouterModel.from_dict(router.to_dict()).artifact_digest() == first
    router.model.coef[0] += 1e-6
    assert router.artifact_digest() != first                 # a real change moves it

    tree_router = RouterModel(
        "tree", ["f0", "f1"], None, DecisionTree(max_depth=2, min_samples_leaf=8).fit(*_xor_data())
    )
    assert tree_router.coefficients() is None
    assert tree_router.predict_proba([{"f0": 0.0, "f1": 1.0}]) == [0.9]
    with pytest.raises(ValueError):
        RouterModel("logistic", ["f0"], None, tree_router.model)


def test_router_roundtrip_predictions_are_exact():
    router = _fitted_router()
    rows = [{"n_violations": float(i), "output_tokens": 10.0 + i} for i in range(4)]
    back = RouterModel.from_dict(router.to_dict())
    assert back.predict_proba(rows) == router.predict_proba(rows)
    assert back.standardizer is not None
    assert back.standardizer.stds == router.standardizer.stds


def test_artifact_digest_is_stable_across_processes():
    """§ 13 identifies a frozen router by this hash, so it must not depend on a
    per-process hash seed or on dict insertion order in a fresh interpreter."""
    router = _fitted_router()
    here = router.artifact_digest()
    script = (
        "import json,sys;"
        "from fis_platform.routing.learn import RouterModel;"
        "print(RouterModel.from_dict(json.loads(sys.argv[1])).artifact_digest())"
    )
    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONHASHSEED="random")
    out = subprocess.run(
        [sys.executable, "-c", script, canonical_json(router.to_dict())],
        cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=60, check=True,
    )
    assert out.stdout.strip() == here
