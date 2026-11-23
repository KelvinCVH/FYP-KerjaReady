"""Build the input for each role skill explanation, one file per role (KR-100).

For every role and skill pair in the role profiles, picks up to MAX_LINES posting lines that mention the skill,
each from a different posting of that role (full lines of at least MIN_WORDS words first, then the newest), and
the skills those same postings ask for most often. Each record also holds the finished message from
build_prompt, which Claude in Claude Code answers with one explanation.

Usage (from the repo root):
    python knowledge-base-pipeline/prepare_skill_explanation_inputs.py data/clean/role-skills.csv
        data/clean/posting-skills.csv data/clean/clean-job-postings.csv data/skill-explanations

Output: <output_dir>/inputs/<role>.jsonl, such as inputs/backend-developer.jsonl
"""

import argparse
import json
import re
from pathlib import Path

import pandas as pd

from skill_explanation_prompt import MAX_LINES, MAX_RELATED, build_prompt

MIN_WORDS = 8
MAX_LINE_CHARS = 300
# A related skill must appear in at least this many of the postings, so one odd posting is not shown as a pattern
MIN_RELATED_POSTINGS = 2

LEADING_BULLET = re.compile(r"^[^A-Za-z0-9(\"'\s]\s*")
EMAIL = re.compile(r"\S+@\S+\.\S+")
LINK = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
SPACES = re.compile(r"\s+")


def role_file_name(role):
    """UI/UX Designer -> ui-ux-designer"""
    return re.sub(r"[^a-z0-9]+", "-", role.lower()).strip("-")


def clean_line(text):
    """One tidy line: no leading bullet, contact details or links, and at most MAX_LINE_CHARS characters."""
    text = SPACES.sub(" ", LEADING_BULLET.sub("", str(text).strip()))
    text = LINK.sub("[link]", EMAIL.sub("[email]", text))
    if len(text) > MAX_LINE_CHARS:
        text = text[:MAX_LINE_CHARS].rsplit(" ", 1)[0] + " ..."
    return text


def is_full_line(text):
    """At least MIN_WORDS words, and not mostly a comma-separated list of skill names."""
    words = len(text.split())
    commas = text.count(",")
    return words >= MIN_WORDS and not (commas >= 3 and words / (commas + 1) < 3)


def choose_lines(matches):
    """matches: this pair's rows of posting-skills, with listing_date. Returns (posting_id, text) pairs."""
    rows = matches.assign(text=matches["evidence_line"].map(clean_line))
    rows = rows.assign(full=rows["text"].map(is_full_line), key=rows["text"].str.lower())
    rows = rows.sort_values(["full", "listing_date", "job_id"], ascending=[False, False, True])
    rows = rows.drop_duplicates("job_id").drop_duplicates("key")
    return [(int(job_id), text) for job_id, text in rows[["job_id", "text"]].head(MAX_LINES).itertuples(index=False)]


def related_skills(posting_skills, role, skill, job_ids):
    """The other skills the same postings ask for, most often first."""
    others = posting_skills[
        (posting_skills["role_title"] == role)
        & posting_skills["job_id"].isin(job_ids)
        & (posting_skills["skill"] != skill)
    ]
    counts = others.groupby("skill")["job_id"].nunique().reset_index(name="postings")
    counts = counts[counts["postings"] >= MIN_RELATED_POSTINGS]
    counts = counts.sort_values(["postings", "skill"], ascending=[False, True]).head(MAX_RELATED)
    return [(name, int(postings)) for name, postings in counts.itertuples(index=False)]


def build_records(role_skills, posting_skills, postings):
    posting_skills = posting_skills.merge(postings[["job_id", "listing_date"]], on="job_id", how="left")
    records = []
    for row in role_skills.sort_values(["role_title", "posting_count"], ascending=[True, False]).itertuples():
        matches = posting_skills[(posting_skills["role_title"] == row.role_title) & (posting_skills["skill"] == row.skill)]
        lines = choose_lines(matches)
        related = related_skills(posting_skills, row.role_title, row.skill, matches["job_id"].unique())
        records.append({
            "role": row.role_title,
            "skill": row.skill,
            "skill_postings": int(row.posting_count),
            "role_postings": int(row.role_postings),
            "lines": [{"posting_id": posting_id, "text": text} for posting_id, text in lines],
            "related": [{"skill": name, "postings": count} for name, count in related],
            "prompt": build_prompt(row.role_title, row.skill, int(row.posting_count), int(row.role_postings),
                                   lines, related),
        })
    return records


def main():
    parser = argparse.ArgumentParser(description="Build the inputs for the role skill explanations.")
    parser.add_argument("role_skills_csv")
    parser.add_argument("posting_skills_csv")
    parser.add_argument("postings_csv")
    parser.add_argument("output_dir")
    args = parser.parse_args()

    records = build_records(
        pd.read_csv(args.role_skills_csv), pd.read_csv(args.posting_skills_csv), pd.read_csv(args.postings_csv)
    )
    inputs = Path(args.output_dir) / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    for role in sorted({record["role"] for record in records}):
        role_records = [record for record in records if record["role"] == role]
        path = inputs / f"{role_file_name(role)}.jsonl"
        with path.open("w", encoding="utf-8") as file:
            for record in role_records:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"{path.name}: {len(role_records)} skills")

    thin = [r for r in records if sum(is_full_line(line["text"]) for line in r["lines"]) < 2]
    print(f"{len(records)} role skills in all; {len(thin)} have fewer than 2 full posting lines")
    for record in thin:
        print(f"  {record['role']} | {record['skill']}: {len(record['lines'])} lines")


if __name__ == "__main__":
    main()