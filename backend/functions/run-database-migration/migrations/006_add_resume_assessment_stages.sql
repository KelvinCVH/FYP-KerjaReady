-- Resume assessment stages, so the app can show which stage a run has reached

-- resumes table: Replace "assessing" with the two stages it covered
ALTER TABLE resumes DROP CONSTRAINT IF EXISTS resumes_status_check;
UPDATE resumes SET status = 'reading' WHERE status = 'assessing';

-- resumes table: Rows that already have ratings are finished
UPDATE resumes SET status = 'done' WHERE status <> 'done' AND resume_id IN (SELECT resume_id FROM resume_ratings);

ALTER TABLE resumes ADD CONSTRAINT resumes_status_check CHECK (status IN ('uploading', 'uploaded', 'reading', 'rating', 'done', 'failed'));
COMMENT ON COLUMN resumes.status IS 'uploading (file not in S3 yet), uploaded, reading, rating, done or failed';

-- resumes table: When the status last changed, so a stalled run can be reported as timed out
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS status_updated_at timestamptz NOT NULL DEFAULT now();
COMMENT ON COLUMN resumes.status_updated_at IS 'When the status last changed';
