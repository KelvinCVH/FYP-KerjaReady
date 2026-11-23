-- Skill matching for skill gap analysis (KR-94)

-- resume_skills table: How each skill was found, so rule-based and semantic matches can be told apart
-- The default only fills rows that already exist; every insert sets the method itself
ALTER TABLE resume_skills ADD COLUMN IF NOT EXISTS match_method varchar(10) NOT NULL DEFAULT 'lexical';
ALTER TABLE resume_skills ALTER COLUMN match_method DROP DEFAULT;
ALTER TABLE resume_skills DROP CONSTRAINT IF EXISTS resume_skills_match_method_check;
-- NOT VALID: this file reruns on every deploy, and 008 has since added 'implied' to these values
ALTER TABLE resume_skills ADD CONSTRAINT resume_skills_match_method_check CHECK (match_method IN ('lexical', 'semantic')) NOT VALID;
COMMENT ON COLUMN resume_skills.match_method IS 'lexical (a vocabulary alias appears in the line) or semantic (the line is close in meaning to the skill)';