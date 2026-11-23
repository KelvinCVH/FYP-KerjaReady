import json

import pytest

from conftest import FakeDatabase, load_function

process_resume = load_function("process-resume")

BUCKET = "kerjaready-resumes"
KEY = "resumes/11111111-1111-1111-1111-111111111111/abc.pdf"
RATINGS = {"a1": 3, "a2": 1, "a3": 2, "b2": 2, "a1_work_link": None, "b2_errors": [], "model_version": "v1"}
SKILLS = [
    {"skill": "Python", "evidence": "Skills: Python, SQL", "method": "lexical"},
    {"skill": "Data visualisation", "evidence": "Built Power BI dashboards for sales", "method": "semantic"},
]
MATCHED = {"skills": SKILLS, "skill_embedding_version": "kerjaready-skill-embedding-test"}


def s3_event(key=KEY):
    return {"Records": [{"s3": {"bucket": {"name": BUCKET}, "object": {"key": key}}}]}


class Pipeline:
    """Fakes the database and assess-resume. extract, rate and match are answers or exceptions to raise."""

    def __init__(self, monkeypatch, extract=None, rate=None, match=None, claimable=True, assessed=True):
        self.assess_calls = []
        self.extract = extract if extract is not None else {"text": "resume text", "pdf_links": []}
        self.rate = rate if rate is not None else RATINGS
        self.match = match if match is not None else MATCHED
        self.claimed = not claimable

        def answer(sql, params):
            if "status = 'reading'" in sql and "RETURNING" in sql:
                if self.claimed:
                    return []
                self.claimed = True
                return [{"resume_id": 7, "s3_key": KEY}]
            if sql.startswith("SELECT extracted_text FROM resumes"):
                return [{"extracted_text": "resume text"}] if assessed else []
            if sql.startswith("INSERT INTO resume_skills"):
                return [{"skill_id": number} for number, _ in enumerate(json.loads(params["skills"]))]
            return []

        self.database = FakeDatabase(answer)
        monkeypatch.setattr(process_resume, "run_query", self.database)
        monkeypatch.setattr(process_resume, "assess", self.fake_assess)
        # set_status lives in the shared module and calls its own run_query
        monkeypatch.setattr("kerjaready_shared.resume_status.run_query", self.database)
        monkeypatch.setenv("RESUME_BUCKET_NAME", BUCKET)

    def fake_assess(self, payload):
        self.assess_calls.append(payload)
        result = {"extract": self.extract, "match_skills": self.match}.get(payload.get("action"), self.rate)
        if isinstance(result, Exception):
            raise result
        return result

    def statuses(self):
        """The status set by each set_status call, in order."""
        return [
            (params["status"], params.get("failure_reason"))
            for sql, params in self.database.queries
            if sql.startswith("UPDATE resumes SET status = :status")
        ]

    def skill_queries(self):
        return [(sql, params) for sql, params in self.database.queries if "resume_skills" in sql]


def test_s3_upload_runs_reading_then_rating_then_done(monkeypatch):
    pipeline = Pipeline(monkeypatch)
    process_resume.handler(s3_event())

    assert pipeline.statuses() == [("rating", None), ("done", None)]
    assert [call.get("action") for call in pipeline.assess_calls] == ["extract", None, "match_skills"]
    upsert = next(sql for sql, _ in pipeline.database.queries if sql.startswith("INSERT INTO resume_ratings"))
    assert "ON CONFLICT (resume_id) DO UPDATE SET" in upsert


def test_s3_claim_sets_reading_and_restarts_the_stale_clock_in_one_update(monkeypatch):
    pipeline = Pipeline(monkeypatch)
    process_resume.handler(s3_event())

    sql, params = pipeline.database.queries[0]
    assert sql.startswith("UPDATE resumes SET status = 'reading', status_updated_at = NOW()")
    assert "WHERE s3_key = :s3_key AND status = 'uploading' RETURNING resume_id" in sql
    assert params == {"s3_key": KEY}


def test_direct_call_claims_the_retried_row_and_restarts_the_stale_clock(monkeypatch):
    pipeline = Pipeline(monkeypatch)
    process_resume.handler({"resume_id": 7})

    sql, params = pipeline.database.queries[0]
    assert sql.startswith("UPDATE resumes SET status = 'reading', status_updated_at = NOW()")
    assert "WHERE resume_id = :resume_id AND status = 'uploaded' RETURNING s3_key" in sql
    assert params == {"resume_id": 7}
    assert pipeline.assess_calls[0] == {"action": "extract", "bucket": BUCKET, "key": KEY}
    assert pipeline.statuses()[-1] == ("done", None)


def test_set_status_restarts_the_stale_clock(monkeypatch):
    pipeline = Pipeline(monkeypatch)
    process_resume.handler(s3_event())

    status_updates = [sql for sql, _ in pipeline.database.queries if sql.startswith("UPDATE resumes SET status")]
    assert status_updates
    assert all("status_updated_at = NOW()" in sql for sql in status_updates)


def test_duplicate_s3_event_starts_only_one_run(monkeypatch):
    pipeline = Pipeline(monkeypatch)
    process_resume.handler(s3_event())
    process_resume.handler(s3_event())

    # One extract, one rate and one match, from the first event only
    assert len(pipeline.assess_calls) == 3
    assert pipeline.statuses() == [("rating", None), ("done", None)]


def test_nothing_to_claim_does_not_call_assess(monkeypatch):
    pipeline = Pipeline(monkeypatch, claimable=False)
    process_resume.handler({"resume_id": 7})

    assert pipeline.assess_calls == []
    assert pipeline.statuses() == []


@pytest.mark.parametrize("code", ["not_pdf", "no_text"])
def test_unreadable_file_fails_with_its_code(monkeypatch, code):
    pipeline = Pipeline(monkeypatch, extract={"error": code})
    process_resume.handler(s3_event())

    assert pipeline.statuses() == [("failed", code)]
    assert len(pipeline.assess_calls) == 1


def test_reading_exception_fails_with_error_and_is_not_raised(monkeypatch):
    pipeline = Pipeline(monkeypatch, extract=RuntimeError("container crashed"))
    process_resume.handler(s3_event())  # no exception

    assert pipeline.statuses() == [("failed", "error")]


def test_rating_exception_fails_with_error_and_is_not_raised(monkeypatch):
    pipeline = Pipeline(monkeypatch, rate=RuntimeError("model failed"))
    process_resume.handler(s3_event())  # no exception

    assert pipeline.statuses() == [("rating", None), ("failed", "error")]


def test_skills_replace_the_old_rows_and_are_saved_before_done(monkeypatch):
    pipeline = Pipeline(monkeypatch)
    process_resume.handler(s3_event())

    assert pipeline.assess_calls[2] == {"action": "match_skills", "text": "resume text"}
    (delete, delete_params), (insert, insert_params) = pipeline.skill_queries()
    assert delete.startswith("DELETE FROM resume_skills WHERE resume_id = :resume_id") and delete_params == {"resume_id": 7}
    assert "JOIN skills s ON s.name = m.skill" in insert
    assert insert_params["resume_id"] == 7 and json.loads(insert_params["skills"]) == SKILLS
    queries = [sql for sql, _ in pipeline.database.queries]
    done = next(i for i, (sql, params) in enumerate(pipeline.database.queries) if params.get("status") == "done")
    assert queries.index(insert) < done


def test_no_skills_only_clears_the_old_rows(monkeypatch):
    pipeline = Pipeline(monkeypatch, match={"skills": [], "skill_embedding_version": "v"})
    process_resume.handler(s3_event())

    assert [sql.split(" ")[0] for sql, _ in pipeline.skill_queries()] == ["DELETE"]
    assert pipeline.statuses()[-1] == ("done", None)


def test_skill_matching_exception_fails_with_error_and_is_not_raised(monkeypatch):
    pipeline = Pipeline(monkeypatch, match=RuntimeError("matching failed"))
    process_resume.handler(s3_event())  # no exception

    assert pipeline.statuses() == [("rating", None), ("failed", "error")]
    assert pipeline.skill_queries() == []


def test_match_skills_again_saves_skills_and_leaves_the_status(monkeypatch):
    pipeline = Pipeline(monkeypatch)
    result = process_resume.handler({"match_skills": 7})

    assert pipeline.assess_calls == [{"action": "match_skills", "text": "resume text"}]
    assert len(pipeline.skill_queries()) == 2
    assert pipeline.statuses() == []
    assert not any(sql.startswith("INSERT INTO resume_ratings") for sql, _ in pipeline.database.queries)
    assert result == {"resume_id": 7, "saved": 2, "lexical": 1, "implied": 0, "semantic": 1,
                      "skill_embedding_version": "kerjaready-skill-embedding-test"}


def test_match_skills_again_skips_a_resume_that_is_not_assessed(monkeypatch):
    pipeline = Pipeline(monkeypatch, assessed=False)
    result = process_resume.handler({"match_skills": 7})

    select_sql, params = pipeline.database.queries[0]
    assert "status = 'done'" in select_sql and params == {"resume_id": 7}
    assert result == {"resume_id": 7, "skipped": "not an assessed resume"}
    assert pipeline.assess_calls == [] and pipeline.skill_queries() == []