-- Guidance agent runs (KR-97): one row for each run, with what it produced and what it used

-- agent_runs table: One run of the guidance agent for a resume and the candidate's target role
CREATE TABLE IF NOT EXISTS agent_runs(
    run_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id uuid NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    resume_id bigint NOT NULL REFERENCES resumes (resume_id) ON DELETE CASCADE,
    role_id bigint NOT NULL REFERENCES roles (role_id) ON DELETE CASCADE,
    output_type varchar(20) NOT NULL CHECK (output_type IN ('smoke_test', 'roadmap')),
    status varchar(10) NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'done', 'failed')),
    model_id varchar(100) NOT NULL,
    prompt_version varchar(50) NOT NULL,
    tool_calls integer NOT NULL DEFAULT 0,
    input_tokens integer,
    output_tokens integer,
    output jsonb,
    error varchar(300),
    created_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz
);
CREATE INDEX IF NOT EXISTS agent_runs_latest_idx ON agent_runs (resume_id, role_id, output_type, created_at DESC);
COMMENT ON TABLE agent_runs IS 'One run of the guidance agent, with its output, model, prompt version, tool calls and token use';