-- Drop indexes
DROP INDEX IF EXISTS idx_login_attempts_successful;
DROP INDEX IF EXISTS idx_login_attempts_email_time;

-- Drop login_attempts table
DROP TABLE IF EXISTS login_attempts;
