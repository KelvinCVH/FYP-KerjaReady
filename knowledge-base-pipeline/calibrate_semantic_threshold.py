"""Choose the semantic skill match score and threshold from the hand-labelled pairs (KR-94).

For each score ("raw" cosine similarity and "relative", how far a skill stands out on a line), a unit counts as
matched when its best line reaches the threshold, and as correct when that line is labelled 1. Precision and
recall are weighted by the sampling weights from draw_skill_match_pairs.py. Recall counts a unit as evidenced
when either of its labelled lines is 1, so it is recall within the lines the matcher considered.

The chosen threshold is the lowest one whose precision reaches the target, with at least MIN_UNITS labelled units
at or above it. Precision is favoured: a wrong "Evidenced" hides a real gap from the candidate.

Usage (from the repo root):
    python knowledge-base-pipeline/calibrate_semantic_threshold.py data/skill-match-calibration

Outputs (in the same folder)
    calibration_curve.csv    score, threshold, units at or above it, weighted precision and recall
    calibration_result.json  chosen score and threshold, with precision, recall and sample counts for the IR
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

SCORES = ["raw", "relative"]
MIN_UNITS = 10


def read_labels(folder):
    pairs = pd.read_csv(folder / "pairs_to_label.csv", dtype=str, keep_default_na=False, encoding="utf-8-sig")
    unlabelled = pairs[~pairs["evidenced"].str.strip().isin(["0", "1"])]
    if len(unlabelled):
        sys.exit(f"{len(unlabelled)} pairs are not labelled 1 or 0, e.g. {unlabelled['pair_id'].head(5).tolist()}")
    return dict(zip(pairs["pair_id"], pairs["evidenced"].str.strip().astype(int)))


def curve(units, score):
    """Weighted precision and recall at every threshold that is one of the units' scores."""
    evidenced_weight = (units["weight"] * units["evidenced"]).sum()
    rows = []
    for threshold in sorted(units[f"{score}_score"].unique()):
        matched = units[units[f"{score}_score"] >= threshold]
        true_positive = (matched["weight"] * matched[f"{score}_correct"]).sum()
        rows.append({
            "score": score,
            "threshold": threshold,
            "units": len(matched),
            "precision": round(true_positive / matched["weight"].sum(), 4),
            "recall": round(true_positive / evidenced_weight, 4) if evidenced_weight else 0.0,
        })
    return pd.DataFrame(rows)


def choose(points, target):
    """Lowest threshold meeting the target precision with enough labelled units, or None."""
    passing = points[(points["precision"] >= target) & (points["units"] >= MIN_UNITS)]
    if passing.empty:
        return None
    row = passing.sort_values("threshold").iloc[0].to_dict()
    return {key: value.item() if hasattr(value, "item") else value for key, value in row.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("--target-precision", type=float, default=0.80)
    args = parser.parse_args()

    folder = Path(args.folder)
    labels = read_labels(folder)
    units = pd.read_csv(folder / "pairs_key.csv", keep_default_na=False)
    for score in SCORES:
        units[f"{score}_correct"] = units[f"{score}_pair_id"].map(labels)
    units["evidenced"] = units[["raw_correct", "relative_correct"]].max(axis=1)

    points = pd.concat([curve(units, score) for score in SCORES], ignore_index=True)
    points.to_csv(folder / "calibration_curve.csv", index=False)

    choices = {score: choose(points[points["score"] == score], args.target_precision) for score in SCORES}
    usable = {score: choice for score, choice in choices.items() if choice}
    best = max(usable.values(), key=lambda c: (c["recall"], c["score"] == "relative")) if usable else None
    result = {
        "target_precision": args.target_precision,
        "labelled_pairs": len(labels),
        "positive_pairs": int(sum(labels.values())),
        "units": len(units),
        "per_score": choices,
        "chosen": best,
    }
    (folder / "calibration_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"{len(labels)} labelled pairs ({result['positive_pairs']} evidenced), {len(units)} units, "
          f"target precision {args.target_precision}")
    for score, choice in choices.items():
        if choice:
            print(f"  {score:<9} threshold {choice['threshold']:.4f}  precision {choice['precision']:.3f}  "
                  f"recall {choice['recall']:.3f}  ({choice['units']} labelled units at or above)")
        else:
            print(f"  {score:<9} no threshold reaches the target with {MIN_UNITS}+ units")
    if best:
        print(f"Chosen: SEMANTIC_SCORE = \"{best['score']}\", SEMANTIC_THRESHOLD = {best['threshold']:.4f}")
    else:
        print("Chosen: none. Keep semantic matching off (SEMANTIC_THRESHOLD = None).")


if __name__ == "__main__":
    main()