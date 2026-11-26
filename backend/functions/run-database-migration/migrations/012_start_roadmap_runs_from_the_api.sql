-- Roadmap runs started from the page (KR-98): the API creates each run before its agent starts, and only one run of a
-- kind can be running for a resume and role at a time

-- agent_runs table: The model and prompt version are filled in when the agent starts, so a run it never started has none
ALTER TABLE agent_runs ALTER COLUMN model_id DROP NOT NULL;
ALTER TABLE agent_runs ALTER COLUMN prompt_version DROP NOT NULL;

-- agent_runs table: Close runs that stopped while still marked running, so the index below can be created. 360 seconds
-- is STALE_AFTER_SECONDS in kerjaready_shared/roadmap_runs.py, above the agent's 5-minute timeout
UPDATE agent_runs SET status = 'failed', error = 'Stopped before it finished', finished_at = now()
WHERE status = 'running' AND created_at < now() - make_interval(secs => 360);

-- agent_runs table: One running run per resume, role and output type
CREATE UNIQUE INDEX IF NOT EXISTS agent_runs_one_running_idx ON agent_runs (resume_id, role_id, output_type)
WHERE status = 'running';
COMMENT ON INDEX agent_runs_one_running_idx IS 'Allows one running run per resume, role and output type';