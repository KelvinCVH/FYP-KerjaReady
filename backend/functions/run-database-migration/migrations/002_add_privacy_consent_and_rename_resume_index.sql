-- Record when each user agreed to the privacy notice
ALTER TABLE users ADD COLUMN IF NOT EXISTS privacy_consented_at timestamptz NOT NULL;

-- Drop the old index name
DROP INDEX IF EXISTS resume_candidate_id_index;