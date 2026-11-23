-- Implied skill matches for skill gap analysis (KR-94)

-- resume_skills table: A broader skill implied by a tool found in the resume (PyTorch -> Machine learning)
ALTER TABLE resume_skills DROP CONSTRAINT IF EXISTS resume_skills_match_method_check;
ALTER TABLE resume_skills ADD CONSTRAINT resume_skills_match_method_check CHECK (match_method IN ('lexical', 'implied', 'semantic'));
COMMENT ON COLUMN resume_skills.match_method IS 'lexical (a vocabulary alias appears in the line), implied (a skill found in the line implies this broader one) or semantic (the line is close in meaning to the skill)';