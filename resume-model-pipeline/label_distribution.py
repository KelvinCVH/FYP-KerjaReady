"""Show how LLM labels are spread across levels, overall and by dataset category.

  python label_distribution.py labels\\pool_sonnet46_p4.jsonl
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

CRITERIA = ["a1", "a2", "a3", "b2"]


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("jsonl")
    args = p.parse_args(argv)
    path = Path(args.jsonl)
    if not path.exists():
        sys.exit(f"Not found: {path.resolve()}\nRun this from the folder that contains 'labels', or pass the full path.")

    d = pd.read_json(path, lines=True)
    d = d[d["status"] == "ok"].drop_duplicates("resume_id", keep="last")
    in_scope = d[~d["out_of_scope"].astype(bool)]
    print(f"{len(d)} labelled, {len(d) - len(in_scope)} out of scope, {len(in_scope)} in scope\n")

    counts = pd.DataFrame({c.upper(): in_scope[c].astype(int).value_counts().reindex(range(4), fill_value=0)
                           for c in CRITERIA})
    counts.index.name = "level"
    share = (counts / len(in_scope) * 100).round(1)
    print("In-scope resumes per level (count, then %)")
    print(counts.to_string())
    print(share.to_string(), "\n")

    print("Out of scope by category")
    print(d.groupby("category")["out_of_scope"].agg(out_of_scope="sum", labelled="count").to_string(), "\n")

    print("Median level by category (in scope)")
    print(in_scope.groupby("category")[CRITERIA].median().to_string())


if __name__ == "__main__":
    main()