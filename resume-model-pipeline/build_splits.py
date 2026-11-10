"""KR-200: build the train, validation and test splits and the label distribution report.

Train and validation come from the labelled pool (in-scope resumes only), split with a fixed seed
and stratified by A2 and A3, so the rare levels appear in both. The test split is the separate
100-resume test set. Out-of-scope resumes are left out, because the rubric does not apply to them.

  python build_splits.py

Outputs
  data/splits/train.csv, val.csv, test.csv   resume_id, category, token_count, a1, a2, a3, b2, label_source, text
  reports/label_distribution.csv             split, criterion, level, count, percent
  reports/label_distribution.json            the same counts plus how the splits were made
"""

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

CRITERIA = ["a1", "a2", "a3", "b2"]
SEED = 200
VAL_SHARE = 0.15
MIN_STRATUM = 5  # smaller A2 x A3 groups are merged into one "rare" group before splitting


def read_labels(path, source_name):
    path = Path(path)
    if not path.exists():
        sys.exit(f"Not found: {path.resolve()}")
    d = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = {"resume_id", "category", *CRITERIA, "out_of_scope"} - set(d.columns)
    if missing:
        sys.exit(f"{path} is missing columns: {sorted(missing)}")
    if "label_source" not in d.columns:
        d["label_source"] = source_name + (" (" + d["prompt_version"] + ")" if "prompt_version" in d.columns else "")
    d["out_of_scope"] = d["out_of_scope"].str.strip().isin(["1", "True", "true"])
    return d


def in_scope_with_text(labels, text_path, name):
    texts = pd.read_csv(text_path, dtype=str, keep_default_na=False)
    keep = [c for c in ["resume_id", "token_count", "text"] if c in texts.columns]
    merged = labels.merge(texts[keep], on="resume_id", how="left")
    no_text = merged["text"].isna() | (merged["text"] == "")
    if no_text.any():
        sys.exit(f"{name}: {int(no_text.sum())} labelled resumes have no text in {text_path}, "
                 f"e.g. {merged.loc[no_text, 'resume_id'].head(3).tolist()}")
    oos = merged["out_of_scope"]
    usable = merged[~oos].copy()
    unrated = (usable[CRITERIA] == "").any(axis=1)
    if unrated.any():
        sys.exit(f"{name}: {int(unrated.sum())} in-scope resumes have a blank rating, "
                 f"e.g. {usable.loc[unrated, 'resume_id'].head(3).tolist()}")
    for c in CRITERIA:
        usable[c] = usable[c].astype(float).astype(int)
    return usable, int(oos.sum())


def stratum_keys(d):
    a2 = d["a2"].clip(upper=2).astype(str).replace({"2": "2+"})
    key = "A2=" + a2 + "|A3=" + d["a3"].astype(str)
    counts = key.value_counts()
    return key.where(key.map(counts) >= MIN_STRATUM, "rare")


def stratified_split(d, val_share, seed):
    """Per stratum, shuffle with the seed and send round(n * val_share) resumes to validation."""
    rng = random.Random(seed)
    keys = stratum_keys(d)
    val_ids = []
    for key in sorted(keys.unique()):
        ids = sorted(d.loc[keys == key, "resume_id"])
        rng.shuffle(ids)
        val_ids += ids[:round(len(ids) * val_share)]
    is_val = d["resume_id"].isin(val_ids)
    return d[~is_val], d[is_val], keys.value_counts().to_dict()


def distribution(splits):
    rows = []
    for name, d in splits.items():
        for c in CRITERIA:
            counts = d[c].value_counts().reindex(range(4), fill_value=0)
            for level, n in counts.items():
                rows.append({"split": name, "criterion": c.upper(), "level": level, "count": int(n),
                             "percent": round(100 * n / len(d), 1) if len(d) else 0.0})
    return pd.DataFrame(rows)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pool-labels", default="labels/pool_labels_final.csv")
    p.add_argument("--pool-text", default="data/labelling_pool.csv")
    p.add_argument("--test-labels", default="labels/test_labels_final.csv")
    p.add_argument("--test-text", default="data/gold_test.csv")
    p.add_argument("--out-dir", default="data/splits")
    p.add_argument("--report", default="reports/label_distribution")
    p.add_argument("--val-share", type=float, default=VAL_SHARE)
    p.add_argument("--seed", type=int, default=SEED)
    args = p.parse_args(argv)

    pool, pool_oos = in_scope_with_text(read_labels(args.pool_labels, "pool"), args.pool_text, "pool")
    test, test_oos = in_scope_with_text(read_labels(args.test_labels, "test"), args.test_text, "test")
    overlap = set(pool["resume_id"]) & set(test["resume_id"])
    if overlap:
        sys.exit(f"{len(overlap)} resumes are in both the pool and the test set, e.g. {sorted(overlap)[:3]}")

    train, val, strata = stratified_split(pool, args.val_share, args.seed)
    splits = {"train": train, "val": val, "test": test}

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cols = ["resume_id", "category", "token_count", *CRITERIA, "label_source", "text"]
    for name, d in splits.items():
        d[[c for c in cols if c in d.columns]].sort_values("resume_id").to_csv(out / f"{name}.csv", index=False)

    dist = distribution(splits)
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    dist.to_csv(f"{report}.csv", index=False)
    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": args.seed, "val_share": args.val_share,
        "stratified_by": "A2 (0, 1, 2+) x A3 level; groups under %d resumes merged as 'rare'" % MIN_STRATUM,
        "strata_sizes": strata,
        "sizes": {name: len(d) for name, d in splits.items()},
        "out_of_scope_excluded": {"pool": pool_oos, "test": test_oos},
        "label_sources": {name: d["label_source"].value_counts().to_dict() for name, d in splits.items()},
        "categories": {name: d["category"].value_counts().to_dict() for name, d in splits.items()},
        "counts": {name: {c.upper(): d[c].value_counts().reindex(range(4), fill_value=0).astype(int).tolist()
                          for c in CRITERIA} for name, d in splits.items()},
        "note": "B2 labels are kept for reference but were found unreliable in calibration; do not train on them.",
    }
    Path(f"{report}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Pool: {len(pool)} in scope ({pool_oos} out of scope left out). Test: {len(test)} in scope ({test_oos} left out).")
    print(f"Split sizes: train {len(train)}, val {len(val)}, test {len(test)} (seed {args.seed}, val share {args.val_share})\n")
    table = dist.pivot_table(index=["criterion", "level"], columns="split", values="count", aggfunc="sum")[["train", "val", "test"]]
    print(table.to_string())
    print(f"\nWrote {out}/train.csv, val.csv, test.csv and {report}.csv / .json")


if __name__ == "__main__":
    main()