"""
Steps:
  1. Remove exact duplicate resumes.
  2. Drop categories outside the rubric's scope (Recruiter, Project Manager).
  3. Apply the same text preprocessing the live system will use.
  4. Remove duplicates that only differ in whitespace or bullet symbols.
  5. Count DistilBERT (cased) tokens and keep resumes that fit in 8 chunks of 510 tokens.

"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

EXCLUDED_CATEGORIES = {"Recruiter Resumes", "Project Manager Resumes"}
MAX_TOKENS = 8 * 510  # 8 chunks x 510 tokens, matching the model's chunk-and-pool input
TOKENIZER_NAME = "distilbert-base-cased"

# Bullet symbols and the private-use glyphs Word and PDF exports leave behind
BULLET_PATTERN = re.compile("[•●▪■◦‣⁃∙]")
WHITESPACE_PATTERN = re.compile(r"\s+")


def preprocess_resume_text(text: str) -> str:
    """Same cleaning as the live system: join lines, strip bullet symbols, collapse whitespace."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace(" ", " ")
    text = BULLET_PATTERN.sub(" ", text)
    text = WHITESPACE_PATTERN.sub(" ", text)
    return text.strip()


def make_resume_id(text: str) -> str:
    """Stable ID from the cleaned text, so labels can always be joined back."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def count_tokens(texts: list[str], tokenizer) -> list[int]:
    encoded = tokenizer(texts, add_special_tokens=False, truncation=False)["input_ids"]
    return [len(ids) for ids in encoded]


def prepare_corpus(raw: pd.DataFrame, tokenizer) -> tuple[pd.DataFrame, dict]:
    report: dict = {"raw_rows": len(raw)}

    df = raw.drop_duplicates(subset="Text", keep="first")
    report["after_exact_dedup"] = len(df)

    df = df[~df["category"].isin(EXCLUDED_CATEGORIES)]
    report["after_category_filter"] = len(df)
    report["excluded_categories"] = sorted(EXCLUDED_CATEGORIES)

    df = df.assign(text=df["Text"].map(preprocess_resume_text))
    df = df[df["text"].str.len() > 0]
    df = df.drop_duplicates(subset="text", keep="first")
    report["after_cleaned_dedup"] = len(df)

    df = df.assign(token_count=count_tokens(df["text"].tolist(), tokenizer))
    over_limit = df["token_count"] > MAX_TOKENS
    report["dropped_over_token_limit"] = int(over_limit.sum())
    df = df[~over_limit]
    report["final_rows"] = len(df)

    df = df.assign(resume_id=df["text"].map(make_resume_id))
    if df["resume_id"].duplicated().any():
        raise ValueError("resume_id collision; lengthen the hash")

    df = df[["resume_id", "category", "job_title", "token_count", "text"]].reset_index(drop=True)
    report["rows_per_category"] = df["category"].value_counts().to_dict()
    report["token_count"] = {
        k: round(float(v), 1) for k, v in df["token_count"].describe(percentiles=[0.5, 0.9]).items()
    }
    return df, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
    raw = pd.read_csv(args.input)
    corpus, report = prepare_corpus(raw, tokenizer)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    corpus.to_csv(args.output, index=False)
    report_path = args.output.with_name(args.output.stem + "_report.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved {len(corpus)} resumes to {args.output}")


if __name__ == "__main__":
    main()