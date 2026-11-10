"""KR-200: label resumes on rubric v1.0 with a Claude model on Amazon Bedrock.

Each resume is sent with the labelling guide as the system prompt. The model must answer
through the record_ratings tool, giving evidence and a reason before each level.
Results are appended to a JSONL file, so an interrupted run can be restarted with the
same command and only the missing resumes are sent.

Examples (PowerShell, from the resume-model-pipeline folder):
  python label_resumes_with_llm.py --input data/gold_calibration.csv --output labels/cal_haiku.jsonl --model-id <inference profile ID> --dry-run
  python label_resumes_with_llm.py --input data/gold_calibration.csv --output labels/cal_haiku.jsonl --model-id <inference profile ID>
  python label_resumes_with_llm.py --export-csv labels/cal_haiku.csv --output labels/cal_haiku.jsonl
"""

import argparse
import csv
import hashlib
import json
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from resume_structure import readable_view

PROMPT_VERSION = "p5"
CRITERIA = ["a1", "a2", "a3", "b2"]
TOOL_NAME = "record_ratings"

INSTRUCTIONS = """You label resumes for a university research project. Follow the labelling guide below exactly; it overrides your own view of what makes a good resume.

How to work:
- The resume text was flattened when it was collected. Its entries and bullet lines were rebuilt automatically, so the split can be wrong. Count entries using the guide's definition, not the automatic split:
  - A bullet that is only a job title (for example "- Treasury Analyst"), or a bullet that starts with a job title followed by a new job's duties, starts a new entry.
  - Two entries with identical or nearly identical descriptions count as one.
- The summary, skills and education blocks are never entries. Work described only there does not count for A1, A2 or A3, however detailed it is.
- Scope: one entry that describes IT work is enough, whatever the rest of the resume is about. A resume with no entries but an IT summary or skills list is in scope and gets A1, A2 and A3 level 0.
- Rate only what is written. Do not reward length, seniority or the number of technologies.
- For every criterion, quote short evidence from the resume first, then give the reason by applying the guide's rule, then choose the level.
- Use the counting table: state how many entries meet the rule out of the total (for example "4 of 6 entries").
- Answer only by calling the record_ratings tool.

LABELLING GUIDE
"""


CRITERION_NOTES = {
    "a1": "A1 Work Evidence. Count only entries that name a specific piece of work and a named technology; general activities do not count.",
    "a2": "A2 Outcome. State how many entries give a concrete result and whether any entry hints at one. Before giving level 2 or 3, "
          "check each result you counted against the guide's list of things that are not results (tasks, deliverables, sizes, self-praise such as 'Successfully migrated').",
    "a3": "A3 Skill in Use. Before giving level 3, check every entry's Environment line and name any tool that no sentence in that entry explains. "
          "Give level 0 only if no entry sentence names any skill; a skill named in a sentence without its use is level 1.",
    "b2": "B2 Language Quality. Read the whole resume, including the summary and skills, and list every distinct error you find before deciding; say whether the tense is consistent.",
}


def criterion_fields(key, note):
    """Flat fields per criterion (evidence, reason, level). Nested objects were sometimes returned malformed."""
    return {
        f"{key}_evidence": {"type": "string", "description": f"{note} Up to four short quotes (under 20 words each) "
                            "that decide the level, in single quotes and separated by semicolons, or 'none found'. 'n/a' if out of scope."},
        f"{key}_reason": {"type": "string", "description": "Apply the guide's rule in one to three sentences. Where the rule "
                          "counts entries, give the count as 'k of n'; exactly half (3 of 6, 4 of 8) is not more than half."},
        f"{key}_level": {"type": "integer", "enum": [0, 1, 2, 3], "description": "0 if out of scope."},
    }


TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "scope_reason": {"type": "string", "description": "One sentence: does any entry describe work on software, data, networks or IT systems?"},
        "out_of_scope": {"type": "boolean"},
        "entries": {"type": "integer", "minimum": 0, "description": "Number of entries after applying the guide's definition."},
        "entry_notes": {"type": "string", "description": "Which automatic entries you merged, split or ignored, or 'as detected'."},
        **{k: v for c, note in CRITERION_NOTES.items() for k, v in criterion_fields(c, note).items()},
    },
    "required": ["scope_reason", "out_of_scope", "entries", "entry_notes"]
                + [f"{c}_{f}" for c in CRITERION_NOTES for f in ("evidence", "reason", "level")],
}


def guide_version(guide_path, guide_text):
    m = re.search(r"Guide\s+v(\d+(?:\.\d+)*)", guide_text.splitlines()[0] if guide_text else "")
    return ("v" + m.group(1)) if m else Path(guide_path).stem


def build_request(row, guide_text, args):
    view, detected = readable_view(row["text"])
    user = (
        f"Resume ID: {row['resume_id']}\n"
        f"Dataset category (may be wrong): {row.get('category', '')}\n"
        f"Job title in the dataset: {row.get('job_title', '')}\n"
        f"Entries detected automatically: {detected} (check this)\n\n"
        f"<resume>\n{view}\n</resume>"
    )
    system = [{"text": INSTRUCTIONS + guide_text}]
    if not args.no_cache:
        system.append({"cachePoint": {"type": "default"}})
    tool_choice = {"tool": {"name": TOOL_NAME}} if args.tool_choice == "tool" else {args.tool_choice: {}}
    inference = {"maxTokens": args.max_tokens}
    if args.temperature is not None:
        inference["temperature"] = args.temperature
    request = {
        "modelId": args.model_id,
        "system": system,
        "messages": [{"role": "user", "content": [{"text": user}]}],
        "inferenceConfig": inference,
        "toolConfig": {
            "tools": [{"toolSpec": {"name": TOOL_NAME, "description": "Record the rubric ratings for one resume.",
                                    "inputSchema": {"json": TOOL_SCHEMA}}}],
            "toolChoice": tool_choice,
        },
    }
    if args.additional_fields:
        request["additionalModelRequestFields"] = args.additional_fields
    return request, detected


LEVEL_IN_TEXT = re.compile(r'"?level"?\s*[:=]\s*"?([0-3])\b')


def _parse_criterion(value):
    """Return a criterion dict from a dict, a JSON string, or a broken JSON string that still contains its level."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        m = LEVEL_IN_TEXT.search(value)
        if m:  # usually unescaped quotes inside the quoted evidence
            return {"evidence": value, "reason": "(repaired from malformed output)", "level": int(m.group(1))}
    return {}


def normalise(result):
    """Models sometimes return a nested object as a JSON string, or a number as text. Repair both where possible."""
    result = dict(result)
    for key in ["a1", "a2", "a3", "b2"]:
        value = result.get(key)
        if f"{key}_level" in result:  # flat schema (p3 and later)
            value = {"evidence": result.get(f"{key}_evidence", ""), "reason": result.get(f"{key}_reason", ""),
                     "level": result.get(f"{key}_level")}
        result[key] = _parse_criterion(value)
        level = result[key].get("level")
        if isinstance(level, str) and level.strip().isdigit():
            result[key]["level"] = int(level)
    if isinstance(result.get("entries"), str) and result["entries"].strip().isdigit():
        result["entries"] = int(result["entries"])
    if isinstance(result.get("out_of_scope"), str) and result["out_of_scope"].lower() in ("true", "false"):
        result["out_of_scope"] = result["out_of_scope"].lower() == "true"
    return result


def validate(result):
    """Return a list of problems with the tool input, empty if it is usable."""
    problems = []
    if not isinstance(result.get("out_of_scope"), bool):
        problems.append("out_of_scope missing")
    if not isinstance(result.get("entries"), int):
        problems.append("entries missing")
    if result.get("out_of_scope") is False:
        for c in CRITERIA:
            level = (result.get(c) or {}).get("level")
            if level not in (0, 1, 2, 3):
                problems.append(f"{c} level invalid: {level!r}")
    return problems


def label_one(client, row, guide_text, meta, args):
    request, detected = build_request(row, guide_text, args)
    last_problem = ""
    for attempt in (1, 2):
        start = time.time()
        response = client.converse(**request)
        latency = round((time.time() - start) * 1000)
        stop = response.get("stopReason")
        blocks = response.get("output", {}).get("message", {}).get("content", [])
        tool_inputs = [b["toolUse"]["input"] for b in blocks if "toolUse" in b and b["toolUse"].get("name") == TOOL_NAME]
        result = normalise(tool_inputs[0]) if tool_inputs else {}
        problems = validate(result) if tool_inputs else [f"no {TOOL_NAME} call (stopReason={stop})"]
        if stop == "max_tokens":
            problems.append("hit maxTokens")
            request["inferenceConfig"]["maxTokens"] *= 2
        if not problems:
            break
        raw = json.dumps(tool_inputs[0], ensure_ascii=False)[:1500] if tool_inputs else ""
        last_problem = "; ".join(problems) + (f" | raw tool input: {raw}" if raw else "")
    else:
        raise ValueError(f"unusable answer after 2 attempts: {last_problem}")

    oos = result["out_of_scope"]
    record = {
        "resume_id": row["resume_id"],
        "category": row.get("category", ""),
        "status": "ok",
        "out_of_scope": oos,
        "scope_reason": result.get("scope_reason", ""),
        "entries": result.get("entries"),
        "entries_detected": detected,
        "entry_notes": result.get("entry_notes", ""),
    }
    for c in CRITERIA:
        r = result.get(c) or {}
        record[c] = None if oos else r.get("level")
        record[f"{c}_evidence"] = r.get("evidence", "")
        record[f"{c}_reason"] = r.get("reason", "")
    usage = response.get("usage", {})
    record.update(meta, attempts=attempt, stop_reason=stop, latency_ms=latency,
                  input_tokens=usage.get("inputTokens"), output_tokens=usage.get("outputTokens"),
                  cache_read_tokens=usage.get("cacheReadInputTokens"), cache_write_tokens=usage.get("cacheWriteInputTokens"),
                  labelled_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return record


def read_done(path):
    done = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("status") == "ok":
                done.add(rec["resume_id"])
    return done


def export_csv(jsonl_path, csv_path):
    """Keep the latest ok record per resume and write a flat CSV with the label columns first."""
    latest = {}
    for line in Path(jsonl_path).read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec.get("status") == "ok":
            latest[rec["resume_id"]] = rec
    if not latest:
        sys.exit(f"No ok records in {jsonl_path}")
    first = ["resume_id", "category", "a1", "a2", "a3", "b2", "out_of_scope", "entries"]
    rest = sorted({k for r in latest.values() for k in r} - set(first))
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=first + rest)
        w.writeheader()
        for rec in latest.values():
            w.writerow({**rec, "out_of_scope": 1 if rec["out_of_scope"] else ""})
    print(f"Wrote {len(latest)} rows to {csv_path}")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", help="CSV with resume_id, category, job_title, text")
    p.add_argument("--output", required=True, help="JSONL file; existing ok rows are skipped")
    p.add_argument("--model-id", help="Bedrock model ID or inference profile ID/ARN (copy it from your account)")
    p.add_argument("--region", default="ap-southeast-5")
    p.add_argument("--profile", default="kerjaready", help="AWS CLI profile name")
    p.add_argument("--guide", default="labelling_guide_v1_4.md")
    p.add_argument("--limit", type=int, help="Label at most this many new resumes")
    p.add_argument("--sample-seed", type=int,
                   help="Shuffle the input with this seed before --limit, so a partial run is a random sample")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--max-tokens", type=int, default=2000)
    p.add_argument("--temperature", type=lambda s: None if s.lower() == "none" else float(s), default=0.0,
                   help="Default 0. Use 'none' if the model rejects the temperature setting")
    p.add_argument("--tool-choice", choices=["tool", "any", "auto"], default="tool",
                   help="'tool' forces record_ratings; use 'any' if the model rejects a forced tool")
    p.add_argument("--additional-fields", type=json.loads,
                   help="JSON passed as additionalModelRequestFields, for model-specific settings")
    p.add_argument("--no-cache", action="store_true", help="Do not add a prompt-cache point")
    p.add_argument("--dry-run", action="store_true", help="Print the first request and size estimates; call nothing")
    p.add_argument("--export-csv", help="Convert --output JSONL to this CSV and exit")
    args = p.parse_args(argv)
    if not args.export_csv and not (args.input and (args.model_id or args.dry_run)):
        p.error("--input and --model-id are required (or use --dry-run / --export-csv)")
    return args


def make_client(args):
    import boto3
    from botocore.config import Config
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    return session.client("bedrock-runtime", config=Config(retries={"max_attempts": 10, "mode": "adaptive"},
                                                         read_timeout=300))


def main(argv=None, client=None):
    args = parse_args(argv)
    out = Path(args.output)
    if args.export_csv:
        export_csv(out, args.export_csv)
        return

    import pandas as pd
    rows = pd.read_csv(args.input, dtype=str, keep_default_na=False).to_dict("records")
    guide_text = Path(args.guide).read_text(encoding="utf-8")
    meta = {"model_id": args.model_id or "", "guide_version": guide_version(args.guide, guide_text),
            "guide_sha1": hashlib.sha1(guide_text.encode()).hexdigest()[:10], "prompt_version": PROMPT_VERSION,
            "temperature": args.temperature}

    if args.sample_seed is not None:
        random.Random(args.sample_seed).shuffle(rows)
    done = read_done(out)
    todo = [r for r in rows if r["resume_id"] not in done]
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(rows)} resumes in input, {len(done)} already labelled, {len(todo)} to send "
          f"(guide {meta['guide_version']}, prompt {PROMPT_VERSION})")

    if args.dry_run:
        if not todo:
            return
        request, _ = build_request(todo[0], guide_text, args)
        system_chars = len(request["system"][0]["text"]) + len(json.dumps(TOOL_SCHEMA))
        user_chars = [len(build_request(r, guide_text, args)[0]["messages"][0]["content"][0]["text"]) for r in todo]
        print("\n--- user message for", todo[0]["resume_id"], "---\n", request["messages"][0]["content"][0]["text"][:3000])
        print(f"\nRough size (4 characters per token): system and tool ~{system_chars // 4:,} tokens per call; "
              f"resumes ~{sum(user_chars) // 4:,} tokens in total, ~{sum(user_chars) // 4 // len(todo):,} per resume; "
              f"output up to {args.max_tokens} tokens per resume")
        return

    client = client or make_client(args)
    out.parent.mkdir(parents=True, exist_ok=True)
    err_path = out.with_suffix(".errors.jsonl")
    lock = threading.Lock()
    totals = {"ok": 0, "error": 0, "in": 0, "out": 0, "cache_read": 0, "cache_write": 0}

    def write(path, rec):
        with lock, open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(label_one, client, r, guide_text, meta, args): r for r in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            row = futures[fut]
            try:
                rec = fut.result()
                write(out, rec)
                totals["ok"] += 1
                totals["in"] += rec["input_tokens"] or 0
                totals["out"] += rec["output_tokens"] or 0
                totals["cache_read"] += rec["cache_read_tokens"] or 0
                totals["cache_write"] += rec["cache_write_tokens"] or 0
            except Exception as e:  # logged and retried on the next run
                totals["error"] += 1
                write(err_path, {"resume_id": row["resume_id"], "error": f"{type(e).__name__}: {e}",
                                 "at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
                if totals["error"] == 1:
                    print(f"First error ({row['resume_id']}): {type(e).__name__}: {e}")
                    print("  Hints: AccessDenied -> request model access in the Bedrock console; ValidationException about "
                          "temperature -> --temperature none; about toolChoice -> --tool-choice any; about cachePoint -> --no-cache")
            if i % 25 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)} done, {totals['error']} errors")

    print(f"Finished: {totals['ok']} ok, {totals['error']} errors (see {err_path.name}; rerun the same command to retry). "
          f"Tokens: {totals['in']:,} input, {totals['cache_write']:,} written to cache, {totals['cache_read']:,} read from cache, "
          f"{totals['out']:,} output")
    if totals["ok"] and totals["cache_read"] + totals["cache_write"] == 0 and not args.no_cache:
        print("Note: no cache use was reported. The guide is probably shorter than this model's minimum cacheable prompt, "
              "so every call pays for the full prompt. Labels are not affected.")


if __name__ == "__main__":
    main()