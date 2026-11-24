"""Check the role skill explanations written in Claude Code against their inputs (KR-100).

Reads <dir>/inputs/<role>.jsonl and <dir>/outputs/<role>.jsonl, and reports every role skill with no explanation,
every explanation with no input, and every rule an explanation breaks (check_explanation). Exits with 1 while
anything is left to fix, so it can be rerun after each round of rewrites.

With --sample N, once everything passes, also writes <dir>/review-sample.csv: N explanations spread across the
roles, with their source lines and empty columns for the hand check.

With --export PATH, once everything passes, also writes every explanation to one JSON Lines file with its source
lines: the file load_knowledge_base.py loads, committed as knowledge-base-pipeline/skill_explanations.jsonl.

Usage (from the repo root):
    python knowledge-base-pipeline/check_skill_explanations.py data/skill-explanations
    python knowledge-base-pipeline/check_skill_explanations.py data/skill-explanations --role backend-developer
    python knowledge-base-pipeline/check_skill_explanations.py data/skill-explanations --sample 40
    python knowledge-base-pipeline/check_skill_explanations.py data/skill-explanations
        --export knowledge-base-pipeline/skill_explanations.jsonl
"""

import argparse
import json
import random
import sys
from pathlib import Path

import pandas as pd

from skill_explanation_prompt import check_explanation

OUTPUT_FIELDS = ["role", "skill", "why_it_matters", "how_to_show", "source_posting_ids"]
SAMPLE_SEED = 100


def read_jsonl(path):
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def check_role(input_path, output_path):
    """(problem messages, passing explanations) for one role file."""
    inputs = {(r["role"], r["skill"]): r for r in read_jsonl(input_path)}
    if not output_path.exists():
        return [f"{output_path.name}: no outputs yet ({len(inputs)} skills)"], []

    problems, passed, seen = [], [], set()
    for number, reply in enumerate(read_jsonl(output_path), start=1):
        key = (reply.get("role"), reply.get("skill"))
        label = f"{output_path.name} line {number} ({key[0]} | {key[1]})"
        if sorted(reply) != sorted(OUTPUT_FIELDS):
            problems.append(f"{label}: fields must be exactly {', '.join(OUTPUT_FIELDS)}")
            continue
        if key not in inputs:
            problems.append(f"{label}: no input for this role and skill")
            continue
        if key in seen:
            problems.append(f"{label}: this role and skill is explained more than once")
            continue
        seen.add(key)
        record = inputs[key]
        rule_problems = check_explanation(reply, record["prompt"], [line["posting_id"] for line in record["lines"]])
        problems += [f"{label}: {problem}" for problem in rule_problems]
        if not rule_problems:
            passed.append((record, reply))
    problems += [f"{output_path.name}: no explanation for {skill}" for role, skill in inputs if (role, skill) not in seen]
    return problems, passed


def write_sample(passed, size, path):
    """size explanations, spread as evenly as possible across the roles."""
    by_role = {}
    for record, reply in passed:
        by_role.setdefault(record["role"], []).append((record, reply))
    rng = random.Random(SAMPLE_SEED)
    for items in by_role.values():
        rng.shuffle(items)
    chosen, round_number = [], 0
    while len(chosen) < size and any(round_number < len(items) for items in by_role.values()):
        for role in sorted(by_role):
            if round_number < len(by_role[role]) and len(chosen) < size:
                chosen.append(by_role[role][round_number])
        round_number += 1

    rows = []
    for record, reply in chosen:
        lines = {line["posting_id"]: line["text"] for line in record["lines"]}
        rows.append({
            "role": record["role"],
            "skill": record["skill"],
            "why_it_matters": reply["why_it_matters"],
            "how_to_show": reply["how_to_show"],
            "source_lines": " | ".join(f"[{i}] {lines[i]}" for i in reply["source_posting_ids"]),
            "related_skills": ", ".join(f"{r['skill']} ({r['postings']})" for r in record["related"]),
            # Hand check: 1 when every claim is supported by the lines and related skills, else 0
            "grounded": "",
            # Hand check: 1 when how_to_show is a usable resume suggestion, else 0
            "useful_advice": "",
            "notes": "",
        })
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")


def export_explanations(passed, path):
    """One line per explanation, in role and input order, with the text of each source line."""
    with Path(path).open("w", encoding="utf-8", newline="\n") as file:
        for record, reply in passed:
            lines = {line["posting_id"]: line["text"] for line in record["lines"]}
            file.write(json.dumps({
                "role": record["role"],
                "skill": record["skill"],
                "why_it_matters": reply["why_it_matters"],
                "how_to_show": reply["how_to_show"],
                "sources": [{"posting_id": i, "line": lines[i]} for i in reply["source_posting_ids"]],
            }, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Check the role skill explanations against their inputs.")
    parser.add_argument("folder")
    parser.add_argument("--role", help="check one role file only, such as backend-developer")
    parser.add_argument("--sample", type=int, help="write a hand-check sample of this many explanations")
    parser.add_argument("--export", help="write every explanation with its source lines to this .jsonl file")
    args = parser.parse_args()

    folder = Path(args.folder)
    input_paths = sorted((folder / "inputs").glob("*.jsonl"))
    if args.role:
        input_paths = [path for path in input_paths if path.stem == args.role]
    if not input_paths:
        sys.exit("No input files found: run prepare_skill_explanation_inputs.py first")

    problems, passed = [], []
    for input_path in input_paths:
        role_problems, role_passed = check_role(input_path, folder / "outputs" / input_path.name)
        problems += role_problems
        passed += role_passed
        print(f"{input_path.stem}: {len(role_passed)} passed, {len(role_problems)} problems")

    for problem in problems:
        print(f"  {problem}")
    print(f"{len(passed)} explanations pass; {len(problems)} problems left")
    if problems:
        sys.exit(1)
    if args.sample:
        write_sample(passed, args.sample, folder / "review-sample.csv")
        print(f"Wrote {min(args.sample, len(passed))} explanations to {folder / 'review-sample.csv'}")
    if args.export:
        if args.role:
            sys.exit("--export needs every role: run it without --role")
        export_explanations(passed, args.export)
        print(f"Exported {len(passed)} explanations to {args.export}")


if __name__ == "__main__":
    main()