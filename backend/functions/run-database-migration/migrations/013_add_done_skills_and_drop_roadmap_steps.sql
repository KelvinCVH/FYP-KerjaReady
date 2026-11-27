-- Skills marked done on the Learning Roadmap (KR-99): kept per candidate and skill, so they stay through Regenerate,
-- a new resume and a new target role

-- done_skills table: A row means the candidate has marked the skill done; no row means not done
CREATE TABLE IF NOT EXISTS done_skills(
    candidate_id uuid NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    skill_id bigint NOT NULL REFERENCES skills (skill_id) ON DELETE CASCADE,
    marked_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (candidate_id, skill_id)
);
COMMENT ON TABLE done_skills IS 'Skills a candidate has marked done on their learning roadmap';

-- roadmap_steps table: Never used; roadmaps are saved in agent_runs.output (KR-97). Its CREATE TABLE is gone from 001
DROP TABLE IF EXISTS roadmap_steps;
