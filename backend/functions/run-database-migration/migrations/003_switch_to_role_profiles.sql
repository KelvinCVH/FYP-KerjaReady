-- Knowledge base: role profiles from job postings, without posting chunks

-- posting_chunks table: Removed, because role profiles in role_skills replace chunk retrieval
DROP TABLE IF EXISTS posting_chunks;

-- job_postings table: Use the JobStreet job ID so the load can be re-run safely
ALTER TABLE job_postings ALTER COLUMN posting_id DROP IDENTITY IF EXISTS;
ALTER TABLE job_postings ALTER COLUMN posted_date SET NOT NULL;
COMMENT ON TABLE job_postings IS 'Entry-level Malaysian ICT job postings from JobStreet, each mapped to one target role';

-- roles table: Seed the target technology roles
INSERT INTO roles (title) VALUES
    ('Software Engineer'),
    ('Frontend Developer'),
    ('Backend Developer'),
    ('Full Stack Developer'),
    ('Mobile Developer'),
    ('AI/ML Engineer'),
    ('Data Scientist'),
    ('Data Engineer'),
    ('Data Analyst'),
    ('Business Analyst'),
    ('QA / Software Tester'),
    ('UI/UX Designer'),
    ('Cybersecurity'),
    ('DevOps Engineer'),
    ('Cloud Engineer'),
    ('Network / Systems Engineer')
ON CONFLICT (title) DO NOTHING;