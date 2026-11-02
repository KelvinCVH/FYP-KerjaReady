"""KR-200: agreement between gold labels (CSV) and LLM labels (JSONL from label_resumes_with_llm.py).

Per criterion it reports quadratic weighted kappa (QWK), Gwet's AC2 with quadratic weights,
exact agreement, agreement within one level, the confusion matrix and both label
distributions. Criteria are compared only on resumes that both sides rated in scope.

Kappa falls when nearly all gold labels share one level, even if agreement is high
(the kappa paradox). AC2 is reported because it is less affected by this; read both
next to exact agreement and the distributions.

Example:
  python compare_labels.py --gold data/gold_calibration_labelled.csv --llm labels/cal_haiku.jsonl --out reports/cal_haiku
"""

import argparse
import json
from pathlib import Path

import pandas as pd

CRITERIA = ["a1", "a2", "a3", "b2"]
LEVELS = [0, 1, 2, 3]
QWK_TARGET = 0.60
SKEW_SHARE = 0.75


def confusion(gold, pred, k=4):
    m = [[0] * k for _ in range(k)]
    for g, p in zip(gold, pred):
        m[g][p] += 1
    return m


def quadratic_weighted_kappa(gold, pred, k=4):
    """Cohen's kappa with quadratic disagreement weights; None when chance disagreement is zero."""
    n = len(gold)
    if n == 0:
        return None
    o = confusion(gold, pred, k)
    row = [sum(o[i]) for i in range(k)]
    col = [sum(o[i][j] for i in range(k)) for j in range(k)]
    w = [[(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)]
    observed = sum(w[i][j] * o[i][j] for i in range(k) for j in range(k)) / n
    expected = sum(w[i][j] * row[i] * col[j] for i in range(k) for j in range(k)) / n ** 2
    return None if expected == 0 else 1 - observed / expected


def gwet_ac2_quadratic(gold, pred, k=4):
    """Gwet's AC2 for two raters with quadratic agreement weights (Gwet, 2008, 2014)."""
    n = len(gold)
    if n == 0:
        return None
    o = confusion(gold, pred, k)
    w = [[1 - (i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)]
    pa = sum(w[i][j] * o[i][j] for i in range(k) for j in range(k)) / n
    pi = [(sum(o[c]) + sum(o[r][c] for r in range(k))) / (2 * n) for c in range(k)]
    tw = sum(sum(r) for r in w)
    pe = tw / (k * (k - 1)) * sum(p * (1 - p) for p in pi)
    return None if pe == 1 else (pa - pe) / (1 - pe)


def as_level(v):
    if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "":
        return None
    return int(float(v))


def as_flag(v):
    return str(v).strip().lower() in {"1", "true", "yes", "y", "x"}


def load_llm(path):
    latest = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec.get("status") == "ok":
            latest[rec["resume_id"]] = rec
    return latest


def compare(gold_csv, llm_jsonl, out_prefix=None):
    gold = pd.read_csv(gold_csv, dtype=str, keep_default_na=False)
    llm = load_llm(llm_jsonl)
    joined = [(g, llm[g["resume_id"]]) for g in gold.to_dict("records") if g["resume_id"] in llm]
    report = {"gold": str(gold_csv), "llm": str(llm_jsonl), "gold_rows": len(gold), "llm_rows": len(llm),
              "matched": len(joined), "missing_from_llm": [g for g in gold.resume_id if g not in llm]}
    if joined:
        first = joined[0][1]
        report.update(model_id=first.get("model_id"), guide_version=first.get("guide_version"),
                      prompt_version=first.get("prompt_version"))

    scope_pairs = [(as_flag(g["out_of_scope"]), bool(r["out_of_scope"])) for g, r in joined]
    report["out_of_scope"] = {
        "agree": sum(a == b for a, b in scope_pairs),
        "gold_only": [g["resume_id"] for (g, r), (a, b) in zip(joined, scope_pairs) if a and not b],
        "llm_only": [g["resume_id"] for (g, r), (a, b) in zip(joined, scope_pairs) if b and not a],
    }

    disagreements, report["criteria"] = [], {}
    for c in CRITERIA:
        pairs = [(g, r, as_level(g[c]), r.get(c)) for g, r in joined
                 if not as_flag(g["out_of_scope"]) and not r["out_of_scope"]]
        pairs = [p for p in pairs if p[2] is not None and p[3] is not None]
        gl, pl = [p[2] for p in pairs], [p[3] for p in pairs]
        n = len(pairs)
        qwk = quadratic_weighted_kappa(gl, pl)
        gold_dist = {lv: gl.count(lv) for lv in LEVELS}
        top_share = max(gold_dist.values()) / n if n else 0
        report["criteria"][c] = {
            "n": n,
            "qwk": None if qwk is None else round(qwk, 3),
            "meets_qwk_target": None if qwk is None else qwk >= QWK_TARGET,
            "gwet_ac2": None if not n else round(gwet_ac2_quadratic(gl, pl), 3),
            "exact": round(sum(a == b for a, b in zip(gl, pl)) / n, 3) if n else None,
            "within_1": round(sum(abs(a - b) <= 1 for a, b in zip(gl, pl)) / n, 3) if n else None,
            "gold_distribution": gold_dist,
            "llm_distribution": {lv: pl.count(lv) for lv in LEVELS},
            "gold_skewed": top_share >= SKEW_SHARE,
            "confusion_gold_rows_llm_cols": confusion(gl, pl) if n else [],
        }
        for g, r, a, b in pairs:
            if a != b:
                disagreements.append({"resume_id": g["resume_id"], "criterion": c, "gold": a, "llm": b, "diff": b - a,
                                      "llm_evidence": r.get(f"{c}_evidence", ""), "llm_reason": r.get(f"{c}_reason", ""),
                                      "gold_notes": g.get("notes", "")[:600]})

    entry_pairs = [(as_level(g.get("entries")), r.get("entries")) for g, r in joined]
    entry_pairs = [(a, b) for a, b in entry_pairs if a is not None and b is not None]
    report["entries"] = {"n": len(entry_pairs), "exact": round(sum(a == b for a, b in entry_pairs) / len(entry_pairs), 3)
                         if entry_pairs else None}

    if out_prefix:
        out = Path(out_prefix)
        out.parent.mkdir(parents=True, exist_ok=True)
        Path(f"{out}_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        pd.DataFrame(disagreements, columns=["resume_id", "criterion", "gold", "llm", "diff", "llm_evidence",
                                             "llm_reason", "gold_notes"]).to_csv(f"{out}_disagreements.csv", index=False)
    return report, disagreements


def print_report(report, n_disagree):
    print(f"Model {report.get('model_id')} | guide {report.get('guide_version')} | prompt {report.get('prompt_version')}")
    print(f"Matched {report['matched']} of {report['gold_rows']} gold resumes")
    if report["missing_from_llm"]:
        print(f"  Not labelled by the LLM yet: {len(report['missing_from_llm'])}")
    s = report["out_of_scope"]
    print(f"Out of scope: agree on {s['agree']}/{report['matched']}; gold only {s['gold_only']}; LLM only {s['llm_only']}")
    e = report["entries"]
    if e["n"]:
        print(f"Entry counts: same count on {e['exact']:.0%} of {e['n']} resumes")
    print(f"\n{'':4}{'n':>4}{'QWK':>8}{'AC2':>8}{'exact':>8}{'+-1':>8}   gold 0/1/2/3   LLM 0/1/2/3")
    for c, m in report["criteria"].items():
        fmt = lambda v: "  n/a" if v is None else f"{v:.2f}"
        gd = "/".join(str(m["gold_distribution"][lv]) for lv in LEVELS)
        ld = "/".join(str(m["llm_distribution"][lv]) for lv in LEVELS)
        flag = "  <- gold labels skewed; read QWK with care" if m["gold_skewed"] else ""
        print(f"{c.upper():4}{m['n']:>4}{fmt(m['qwk']):>8}{fmt(m['gwet_ac2']):>8}{fmt(m['exact']):>8}{fmt(m['within_1']):>8}"
              f"   {gd:<14} {ld:<12}{flag}")
    print(f"\nQWK target: {QWK_TARGET}. Disagreements: {n_disagree}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--gold", required=True, help="CSV with resume_id, a1, a2, a3, b2, out_of_scope (and optional entries, notes)")
    p.add_argument("--llm", required=True, help="JSONL written by label_resumes_with_llm.py")
    p.add_argument("--out", help="Prefix for <out>_report.json and <out>_disagreements.csv")
    args = p.parse_args(argv)
    report, disagreements = compare(args.gold, args.llm, args.out)
    print_report(report, len(disagreements))
    if args.out:
        print(f"Wrote {args.out}_report.json and {args.out}_disagreements.csv")


if __name__ == "__main__":
    main()