-- Guidance agent output checks (KR-97): how often the model had to correct its output before it passed

-- agent_runs table: The number of outputs the checks rejected in the run
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS corrections integer NOT NULL DEFAULT 0;
COMMENT ON COLUMN agent_runs.corrections IS 'How many outputs the checks rejected before the run finished or failed';