-- User table: Store the role each candidate is aiming for. Role can only be chosen from KB
ALTER TABLE users ADD COLUMN IF NOT EXISTS target_role_id bigint REFERENCES roles (role_id);
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_target_role_candidate_only;
ALTER TABLE users ADD CONSTRAINT users_target_role_candidate_only CHECK (account_type = 'candidate' OR target_role_id is NULL);
COMMENT ON COLUMN users.target_role_id IS 'Role the candidate is aming for, always null for recruiters';