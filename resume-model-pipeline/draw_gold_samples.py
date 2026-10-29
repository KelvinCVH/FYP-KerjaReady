"""
Splits the corpus into three disjoint files:
  gold_calibration.csv  - 30 resumes to tune the LLM labelling prompt against your labels
  gold_test.csv         - 100 resumes held out as the test set; never used for training or prompt tuning
  labelling_pool.csv    - everything else, to be labelled by the LLM

Both gold samples are stratified by category (proportional, largest-remainder rounding) with a fixed seed,
so the same input always gives the same samples.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

SEED = 200  # fixed for reproducibility (KR-200)
CALIBRATION_SIZE = 30
TEST_SIZE = 100
LABEL_COLUMNS = ["a1", "a2", "a3", "b2", "out_of_scope", "notes"]


def allocate(counts: pd.Series, total: int) -> pd.Series:
    """Proportional allocation per category that sums exactly to `total` (largest-remainder method)."""
    exact = counts / counts.sum() * total
    alloc = exact.astype(int)
    remainder = (exact - alloc).sort_values(ascending=False)
    for category in remainder.index[: total - alloc.sum()]:
        alloc[category] += 1
    return alloc


def draw_samples(corpus: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    counts = corpus["category"].value_counts().sort_index()
    cal_alloc = allocate(counts, CALIBRATION_SIZE)
    test_alloc = allocate(counts, TEST_SIZE)

    calibration_parts, test_parts = [], []
    for category, group in corpus.groupby("category", sort=True):
        n_cal, n_test = int(cal_alloc[category]), int(test_alloc[category])
        picked = group.sample(n=n_cal + n_test, random_state=SEED)
        calibration_parts.append(picked.iloc[:n_cal])
        test_parts.append(picked.iloc[n_cal:])

    calibration = pd.concat(calibration_parts).sample(frac=1, random_state=SEED)  # shuffle across categories
    test = pd.concat(test_parts).sample(frac=1, random_state=SEED)
    gold_ids = set(calibration["resume_id"]) | set(test["resume_id"])
    pool = corpus[~corpus["resume_id"].isin(gold_ids)]
    return calibration, test, pool


def with_label_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Empty columns for manual labels, placed before the long text column."""
    out = df.drop(columns=["text"]).copy()
    for col in LABEL_COLUMNS:
        out[col] = ""
    out["text"] = df["text"].values
    return out.reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    corpus = pd.read_csv(args.input)
    calibration, test, pool = draw_samples(corpus)

    # Safety checks: no overlap, nothing lost
    assert not set(calibration["resume_id"]) & set(test["resume_id"])
    assert len(calibration) + len(test) + len(pool) == len(corpus)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with_label_columns(calibration).to_csv(args.output_dir / "gold_calibration.csv", index=False)
    with_label_columns(test).to_csv(args.output_dir / "gold_test.csv", index=False)
    pool.to_csv(args.output_dir / "labelling_pool.csv", index=False)

    summary = {
        "seed": SEED,
        "calibration": calibration["category"].value_counts().to_dict(),
        "test": test["category"].value_counts().to_dict(),
        "labelling_pool_rows": len(pool),
    }
    (args.output_dir / "gold_samples_report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()