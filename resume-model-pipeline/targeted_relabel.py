"""KR-200: relabel only the resumes a prompt change affects, then merge the two label sets.

Prompt p5 changed the scope rule, the A3 level 0 rule and the A2 checks. Instead of relabelling
everything, relabel only the resumes the first pass put out of scope, at A3 level 0, or at A2
level 2 or 3, and keep the first-pass labels for the rest.

  python targeted_relabel.py select --labels reports\\labels\\pool_sonnet46_p4.jsonl --pool data\\labelling_pool.csv --out data\\relabel_p5.csv
  python label_resumes_with_llm.py --input data\\relabel_p5.csv --output reports\\labels\\relabel_p5.jsonl --model-id global.anthropic.claude-sonnet-4-6
  python targeted_relabel.py merge --base reports\\labels\\pool_sonnet46_p4.jsonl --override reports\\labels\\relabel_p5.jsonl --out reports\\labels\\pool_labels_final.csv
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

LABEL_COLUMNS = ["resume_id", "category", "a1", "a2", "a3", "b2", "out_of_scope", "entries", "prompt_version",
                 "guide_version", "model_id", "label_source"]


def load_ok(path):
    path = Path(path)
    if not path.exists():
        sys.exit(f"Not found: {path.resolve()}")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    d = pd.DataFrame([r for r in rows if r.get("status") == "ok"])
    return d.drop_duplicates("resume_id", keep="last")


def flagged(d):
    oos = d["out_of_scope"].astype(bool)
    return d[oos | (~oos & ((d["a3"] == 0) | (d["a2"] >= 2)))]


def select(args):
    d = load_ok(args.labels)
    f = flagged(d)
    oos = f["out_of_scope"].astype(bool)
    print(f"{len(d)} labelled; to relabel: {len(f)} "
          f"({oos.sum()} out of scope, {(~oos & (f['a3'] == 0)).sum()} at A3 level 0, {(~oos & (f['a2'] >= 2)).sum()} at A2 level 2-3)")
    pool = pd.read_csv(args.pool, dtype=str, keep_default_na=False)
    out = pool[pool["resume_id"].isin(f["resume_id"])]
    missing = set(f["resume_id"]) - set(out["resume_id"])
    if missing:
        sys.exit(f"{len(missing)} flagged resumes are not in {args.pool}, e.g. {sorted(missing)[:3]}")
    out.to_csv(args.out, index=False)
    print(f"Wrote {len(out)} resumes to {args.out}")


def merge(args):
    base = load_ok(args.base).set_index("resume_id")
    override = load_ok(args.override).set_index("resume_id")
    expected = set(flagged(base.reset_index())["resume_id"])
    missing = expected - set(override.index)
    if missing:
        print(f"Warning: {len(missing)} flagged resumes have no relabel yet; rerun the labelling command first.")
    base["label_source"] = "first pass (" + base["prompt_version"] + ")"
    override["label_source"] = "relabel (" + override["prompt_version"] + ")"
    merged = base.copy()
    common = override.index.intersection(base.index)
    merged.loc[common, override.columns] = override.loc[common]
    merged = merged.reset_index()
    merged["out_of_scope"] = merged["out_of_scope"].astype(bool).map({True: 1, False: ""})
    for c in ["a1", "a2", "a3", "b2", "entries"]:
        merged[c] = pd.to_numeric(merged[c], errors="coerce").astype("Int64")
    merged[LABEL_COLUMNS].to_csv(args.out, index=False)

    changed = {c: int((base.loc[common, c].fillna(-1) != override.loc[common, c].fillna(-1)).sum())
               for c in ["out_of_scope", "a1", "a2", "a3", "b2"]}
    print(f"Merged {len(merged)} resumes ({len(common)} relabelled). Changed by the relabel: {changed}")
    ins = merged[merged["out_of_scope"] != 1].dropna(subset=["a1", "a2", "a3", "b2"])
    print(f"{len(merged) - len(ins)} out of scope, {len(ins)} in scope")
    print(pd.DataFrame({c.upper(): ins[c].astype(int).value_counts().reindex(range(4), fill_value=0)
                        for c in ["a1", "a2", "a3", "b2"]}).rename_axis("level").to_string())
    print(f"Wrote {args.out}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select")
    s.add_argument("--labels", required=True)
    s.add_argument("--pool", required=True)
    s.add_argument("--out", required=True)
    m = sub.add_parser("merge")
    m.add_argument("--base", required=True)
    m.add_argument("--override", required=True)
    m.add_argument("--out", required=True)
    args = p.parse_args(argv)
    select(args) if args.cmd == "select" else merge(args)


if __name__ == "__main__":
    main()