"""Sample 10 cleaned postings per role for a manual check of the role mapping.

Usage:
    python knowledge-base-pipeline/sample_role_mapping_check.py \
        data/clean/clean-job-postings.csv data/clean/role-mapping-check.csv --seed 7
"""

import argparse

import pandas as pd

SAMPLE_PER_ROLE = 10


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cleaned_csv")
    parser.add_argument("output_csv")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    postings = pd.read_csv(args.cleaned_csv)
    sample = postings.groupby("role_title").sample(n=SAMPLE_PER_ROLE, random_state=args.seed)
    sample = sample.assign(
        description_start=sample["description"].str.split().str.join(" ").str[:300], correct_role="", entry_level=""
    )
    columns = ["role_title", "job_title", "description_start", "correct_role", "entry_level"]
    sample[columns].to_csv(args.output_csv, index=False)
    print(f"Saved {len(sample)} postings to {args.output_csv}. Fill in correct_role and entry_level with Y or N.")


if __name__ == "__main__":
    main()