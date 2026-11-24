-- Skill explanations (KR-100): why each role asks for a skill and how to show it in a resume, written once
-- from the role's job posting lines and loaded with the knowledge base

-- role_skills table: Two explanation columns, empty until the knowledge base load fills them
ALTER TABLE role_skills ADD COLUMN IF NOT EXISTS why_it_matters text;
ALTER TABLE role_skills ADD COLUMN IF NOT EXISTS how_to_show text;
COMMENT ON COLUMN role_skills.why_it_matters IS 'Why the role asks for the skill, based on its job posting lines';
COMMENT ON COLUMN role_skills.how_to_show IS 'How a candidate who has the skill can show it in a resume';

-- role_skill_sources table: The job posting lines each role skill explanation is based on
CREATE TABLE IF NOT EXISTS role_skill_sources(
    role_id bigint NOT NULL,
    skill_id bigint NOT NULL,
    posting_id bigint NOT NULL REFERENCES job_postings (posting_id) ON DELETE CASCADE,
    line text NOT NULL,
    PRIMARY KEY (role_id, skill_id, posting_id),
    FOREIGN KEY (role_id, skill_id) REFERENCES role_skills (role_id, skill_id) ON DELETE CASCADE
);
COMMENT ON TABLE role_skill_sources IS 'The job posting lines each role skill explanation is based on';