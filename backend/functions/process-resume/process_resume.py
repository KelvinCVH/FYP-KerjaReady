"""
Rate an uploaded resume in the background. Two ways in:
- S3 starts this function for each new PDF under resumes/ (status uploading).
- retry-resume-assessment invokes it with {"resume_id": ...} (status uploaded).

1. Claim the resume with one conditional UPDATE: -> reading. A repeated event finds nothing to claim.
2. kerjaready-assess-resume reads the PDF. The text is saved on the resume row. -> rating
3. kerjaready-assess-resume rates the text and finds the skills it evidences. The ratings are saved in
   resume_ratings and the skills in resume_skills. -> done
Any failure -> failed, with failure_reason not_pdf, no_text or error. Errors are logged and never re-raised:
the async invoke must not retry the run. The candidate retries it with the Retry button.

{"match_skills": <resume_id>} matches the skills of an assessed resume again, without changing its status or
ratings (scripts/rematch_resume_skills.py). Its errors are raised, so the caller sees them.
"""

import json
import os
import traceback
import urllib.parse

import boto3
from botocore.config import Config
from kerjaready_shared.data_api import run_query
from kerjaready_shared.resume_status import (
    DONE,
    ERROR,
    FAILED,
    RATING,
    READING,
    UPLOADED,
    UPLOADING,
    set_status,
)

# A first call can take about a minute while the assessment container starts. The wait stays below this
# function's 110 s timeout. Never retry the call: a retry would start a second container and rate the resume twice.
LAMBDA_CONFIG = Config(read_timeout=100, retries={"total_max_attempts": 1})

_lambda = None


def _client():
    global _lambda
    if _lambda is None:
        _lambda = boto3.client("lambda", config=LAMBDA_CONFIG)
    return _lambda


def _parameters(**values):
    """Data API parameters; None becomes SQL NULL."""
    def value(item):
        if item is None:
            return {"isNull": True}
        if isinstance(item, int):
            return {"longValue": item}
        return {"stringValue": item}

    return [{"name": name, "value": value(item)} for name, item in values.items()]


def assess(payload):
    """Call kerjaready-assess-resume and return its answer."""
    response = _client().invoke(
        FunctionName=os.environ["ASSESS_FUNCTION_NAME"],
        Payload=json.dumps(payload).encode("utf-8"),
    )
    body = json.loads(response["Payload"].read() or b"null")
    if response.get("FunctionError"):
        error_type = body.get("errorType") if isinstance(body, dict) else None
        raise RuntimeError(f"kerjaready-assess-resume failed: {error_type}")
    return body


def save_ratings(resume_id, ratings):
    """Insert or replace, so a retried run never leaves two results."""
    run_query(
        "INSERT INTO resume_ratings "
        "(resume_id, a1_rating, a2_rating, a3_rating, b2_rating, a1_work_link, b2_errors, model_version) "
        "VALUES (:resume_id, :a1, :a2, :a3, :b2, :a1_work_link, CAST(:b2_errors AS jsonb), :model_version) "
        "ON CONFLICT (resume_id) DO UPDATE SET "
        "a1_rating = EXCLUDED.a1_rating, a2_rating = EXCLUDED.a2_rating, a3_rating = EXCLUDED.a3_rating, "
        "b2_rating = EXCLUDED.b2_rating, a1_work_link = EXCLUDED.a1_work_link, b2_errors = EXCLUDED.b2_errors, "
        "model_version = EXCLUDED.model_version, rated_at = NOW()",
        _parameters(
            resume_id=resume_id,
            a1=ratings["a1"],
            a2=ratings["a2"],
            a3=ratings["a3"],
            b2=ratings["b2"],
            a1_work_link=ratings.get("a1_work_link"),
            b2_errors=json.dumps(ratings.get("b2_errors") or []),
            model_version=ratings["model_version"],
        ),
    )


def save_resume_skills(resume_id, skills):
    """Replace the resume's skills. Skill names become skill ids inside the INSERT; returns how many were saved."""
    run_query("DELETE FROM resume_skills WHERE resume_id = :resume_id", _parameters(resume_id=resume_id))
    if not skills:
        return 0
    saved = run_query(
        "INSERT INTO resume_skills (resume_id, skill_id, evidence_excerpt, match_method) "
        "SELECT :resume_id, s.skill_id, m.evidence, m.method "
        "FROM jsonb_to_recordset(CAST(:skills AS jsonb)) AS m(skill text, evidence text, method text) "
        "JOIN skills s ON s.name = m.skill "
        "RETURNING skill_id",
        _parameters(resume_id=resume_id, skills=json.dumps(skills)),
    )
    if len(saved) < len(skills):
        # A skill name missing from the skills table: the vocabulary in the container and the database differ
        print(json.dumps({"resume_id": resume_id, "skills_not_saved": len(skills) - len(saved)}))
    return len(saved)


def match_skills_again(resume_id):
    """Match the skills of an assessed resume again. Status and ratings stay as they are."""
    rows = run_query(
        f"SELECT extracted_text FROM resumes WHERE resume_id = :resume_id AND status = '{DONE}'",
        _parameters(resume_id=resume_id),
    )
    if not rows or not rows[0].get("extracted_text"):
        return {"resume_id": resume_id, "skipped": "not an assessed resume"}
    matched = assess({"action": "match_skills", "text": rows[0]["extracted_text"]})
    methods = [skill["method"] for skill in matched["skills"]]
    result = {
        "resume_id": resume_id,
        "saved": save_resume_skills(resume_id, matched["skills"]),
        "lexical": methods.count("lexical"),
        "implied": methods.count("implied"),
        "semantic": methods.count("semantic"),
        "skill_embedding_version": matched.get("skill_embedding_version"),
    }
    print(json.dumps(result))
    return result


def claim_upload(key):
    """S3 path: claim the row whose file just arrived. Returns the resume id, or None."""
    rows = run_query(
        f"UPDATE resumes SET status = '{READING}', status_updated_at = NOW() "
        f"WHERE s3_key = :s3_key AND status = '{UPLOADING}' RETURNING resume_id",
        _parameters(s3_key=key),
    )
    return rows[0]["resume_id"] if rows else None


def claim_retry(resume_id):
    """Retry path: claim the row the Retry button reset. Returns its S3 key, or None."""
    rows = run_query(
        f"UPDATE resumes SET status = '{READING}', status_updated_at = NOW() "
        f"WHERE resume_id = :resume_id AND status = '{UPLOADED}' RETURNING s3_key",
        _parameters(resume_id=resume_id),
    )
    return rows[0]["s3_key"] if rows else None


def run(resume_id, bucket, key):
    """Read, then rate. Every failure is saved on the row and never re-raised."""
    try:
        extracted = assess({"action": "extract", "bucket": bucket, "key": key})
        if extracted.get("error"):
            set_status(resume_id, FAILED, extracted["error"])
            print(json.dumps({"resume_id": resume_id, "status": FAILED, "reason": extracted["error"]}))
            return
        run_query(
            "UPDATE resumes SET extracted_text = :text WHERE resume_id = :resume_id",
            _parameters(text=extracted["text"], resume_id=resume_id),
        )
        set_status(resume_id, RATING)
    except Exception:
        traceback.print_exc()
        set_status(resume_id, FAILED, ERROR)
        print(json.dumps({"resume_id": resume_id, "status": FAILED, "stage": READING}))
        return

    try:
        ratings = assess({"text": extracted["text"], "pdf_links": extracted.get("pdf_links") or []})
        matched = assess({"action": "match_skills", "text": extracted["text"]})
        save_ratings(resume_id, ratings)
        save_resume_skills(resume_id, matched["skills"])
        set_status(resume_id, DONE)
        print(json.dumps({"resume_id": resume_id, "status": DONE}))
    except Exception:
        traceback.print_exc()
        set_status(resume_id, FAILED, ERROR)
        print(json.dumps({"resume_id": resume_id, "status": FAILED, "stage": RATING}))


def handler(event, context=None):
    if "match_skills" in event:
        return match_skills_again(int(event["match_skills"]))

    if "resume_id" in event:
        resume_id = int(event["resume_id"])
        key = claim_retry(resume_id)
        if key is None:
            print(json.dumps({"skipped": "resume is not waiting for a retry", "resume_id": resume_id}))
            return
        run(resume_id, os.environ["RESUME_BUCKET_NAME"], key)
        return

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        resume_id = claim_upload(key)
        if resume_id is None:
            print(json.dumps({"skipped": "no resume is waiting for this upload"}))
            continue
        run(resume_id, bucket, key)