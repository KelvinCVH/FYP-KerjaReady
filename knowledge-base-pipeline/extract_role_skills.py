"""Extract skills from the cleaned postings and build each role's skill profile.

Usage:
    python knowledge-base-pipeline/extract_role_skills.py data/clean/clean-job-postings.csv
        knowledge-base-pipeline/skill_vocabulary.csv data/clean/posting-skills.csv data/clean/role-skills.csv
"""

import argparse
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "functions" / "assess-resume"))
from skill_matching import find_skills, load_vocabulary

# A skill joins a role profile only when enough of the role's postings ask for it
MIN_POSTINGS = 5
MIN_SHARE = 0.05


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cleaned_csv")
    parser.add_argument("vocabulary_csv")
    parser.add_argument("posting_skills_csv")
    parser.add_argument("role_skills_csv")
    args = parser.parse_args()

    postings = pd.read_csv(args.cleaned_csv)
    vocabulary = load_vocabulary(args.vocabulary_csv)

    rows = []
    for job_id, role_title, description in postings[["job_id", "role_title", "description"]].itertuples(index=False):
        for skill, line in find_skills(description, vocabulary).items():
            rows.append({"job_id": job_id, "role_title": role_title, "skill": skill, "evidence_line": line})
    posting_skills = pd.DataFrame(rows)
    posting_skills.to_csv(args.posting_skills_csv, index=False)
    print(
        f"{len(posting_skills):,} posting-skill pairs; "
        f"{posting_skills['job_id'].nunique():,} of {len(postings):,} postings have at least one skill"
    )

    role_postings = postings["role_title"].value_counts().rename("role_postings")
    profile = posting_skills.groupby(["role_title", "skill"]).size().rename("posting_count").reset_index()
    profile = profile.join(role_postings, on="role_title")
    profile["demand_share"] = (profile["posting_count"] / profile["role_postings"]).round(4)
    profile = profile[(profile["posting_count"] >= MIN_POSTINGS) & (profile["demand_share"] >= MIN_SHARE)]
    profile = profile.sort_values(["role_title", "demand_share"], ascending=[True, False])
    profile.to_csv(args.role_skills_csv, index=False)

    print(f"{len(profile):,} role-skill rows kept (at least {MIN_POSTINGS} postings and {MIN_SHARE:.0%} of the role)")
    summary = profile.groupby("role_title").agg(
        skills=("skill", "size"), top_skills=("skill", lambda skills: ", ".join(skills.head(3)))
    )
    print(summary.to_string())


if __name__ == "__main__":
    main()