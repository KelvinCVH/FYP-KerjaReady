"""Metrics for the rating model: quadratic weighted kappa, macro-F1, exact agreement and a majority-class baseline."""

from collections import Counter

LEVELS = [0, 1, 2, 3]


def quadratic_weighted_kappa(gold, pred, k=4):
    """Cohen's kappa with quadratic weights; None when it is undefined (one level only)."""
    n = len(gold)
    if n == 0:
        return None
    o = [[0] * k for _ in range(k)]
    for g, p in zip(gold, pred):
        o[g][p] += 1
    row = [sum(o[i]) for i in range(k)]
    col = [sum(o[i][j] for i in range(k)) for j in range(k)]
    w = [[(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)]
    observed = sum(w[i][j] * o[i][j] for i in range(k) for j in range(k)) / n
    expected = sum(w[i][j] * row[i] * col[j] for i in range(k) for j in range(k)) / n ** 2
    return None if expected == 0 else 1 - observed / expected


def macro_f1(gold, pred):
    """Mean F1 over the levels that occur in gold or pred (same rule as scikit-learn's default)."""
    levels = sorted(set(gold) | set(pred))
    scores = []
    for lv in levels:
        tp = sum(g == lv and p == lv for g, p in zip(gold, pred))
        fp = sum(g != lv and p == lv for g, p in zip(gold, pred))
        fn = sum(g == lv and p != lv for g, p in zip(gold, pred))
        scores.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return sum(scores) / len(scores) if scores else None


def criterion_metrics(gold, pred):
    """All metrics for one criterion, rounded for reports."""
    qwk = quadratic_weighted_kappa(gold, pred)
    f1 = macro_f1(gold, pred)
    exact = sum(g == p for g, p in zip(gold, pred)) / len(gold) if gold else None
    return {
        "n": len(gold),
        "qwk": None if qwk is None else round(qwk, 3),
        "macro_f1": None if f1 is None else round(f1, 3),
        "exact": None if exact is None else round(exact, 3),
        "gold_counts": [gold.count(lv) for lv in LEVELS],
        "pred_counts": [pred.count(lv) for lv in LEVELS],
    }


def majority_baseline(train_gold, gold):
    """Predict the most common training level for every resume, and score it the same way."""
    level = Counter(train_gold).most_common(1)[0][0]
    return {"level": level, **criterion_metrics(gold, [level] * len(gold))}