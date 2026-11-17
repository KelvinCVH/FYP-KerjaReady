-- Resume upload and rubric ratings

-- resumes table: The row is created before the upload, so the text is filled in after extraction
ALTER TABLE resumes ALTER COLUMN extracted_text DROP NOT NULL;

-- resumes table: Track the upload and assessment so the app can show progress
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS status varchar(10) NOT NULL DEFAULT 'uploading';
ALTER TABLE resumes DROP CONSTRAINT IF EXISTS resumes_status_check;
-- NOT VALID: this file reruns on every deploy, and 006 has since replaced these values
ALTER TABLE resumes ADD CONSTRAINT resumes_status_check CHECK (status IN ('uploading', 'assessing', 'done', 'failed')) NOT VALID;
COMMENT ON COLUMN resumes.status IS 'uploading, assessing, done or failed';

ALTER TABLE resumes ADD COLUMN IF NOT EXISTS failure_reason varchar(10);
ALTER TABLE resumes DROP CONSTRAINT IF EXISTS resumes_failure_reason_check;
ALTER TABLE resumes ADD CONSTRAINT resumes_failure_reason_check CHECK (failure_reason IN ('not_pdf', 'no_text', 'error'));
COMMENT ON COLUMN resumes.failure_reason IS 'Why the assessment failed, only set when status is failed';

-- resume_ratings table: Rubric ratings from kerjaready-assess-resume, one row per resume
CREATE TABLE IF NOT EXISTS resume_ratings(
    resume_id bigint PRIMARY KEY REFERENCES resumes (resume_id) ON DELETE CASCADE,
    a1_rating smallint NOT NULL CHECK (a1_rating BETWEEN 0 AND 3),
    a2_rating smallint NOT NULL CHECK (a2_rating BETWEEN 0 AND 3),
    a3_rating smallint NOT NULL CHECK (a3_rating BETWEEN 0 AND 3),
    b2_rating smallint NOT NULL CHECK (b2_rating BETWEEN 0 AND 3),
    a1_work_link varchar(500),
    b2_errors jsonb NOT NULL DEFAULT '[]',
    model_version varchar(50) NOT NULL,
    rated_at timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE resume_ratings IS 'Rubric ratings from kerjaready-assess-resume, one row per resume';
COMMENT ON COLUMN resume_ratings.a1_rating IS 'A1 Work Evidence, 0 to 3';
COMMENT ON COLUMN resume_ratings.a2_rating IS 'A2 Outcome, 0 to 3';
COMMENT ON COLUMN resume_ratings.a3_rating IS 'A3 Skill in Use, 0 to 3';
COMMENT ON COLUMN resume_ratings.b2_rating IS 'B2 Language Quality, 0 to 3';
COMMENT ON COLUMN resume_ratings.a1_work_link IS 'Repository, demo or portfolio link that gave A1 level 3';
COMMENT ON COLUMN resume_ratings.b2_errors IS 'Language errors counted for B2';