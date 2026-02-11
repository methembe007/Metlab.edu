-- Create login_attempts table for tracking failed login attempts
CREATE TABLE IF NOT EXISTS login_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    attempt_at TIMESTAMP DEFAULT NOW(),
    successful BOOLEAN DEFAULT false,
    ip_address INET
);

-- Create index on email and attempt_at for lockout checks
CREATE INDEX IF NOT EXISTS idx_login_attempts_email_time ON login_attempts(email, attempt_at DESC);

-- Create index on successful status for filtering
CREATE INDEX IF NOT EXISTS idx_login_attempts_successful ON login_attempts(successful);
