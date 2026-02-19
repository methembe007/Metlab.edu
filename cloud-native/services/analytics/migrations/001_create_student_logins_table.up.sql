-- Create student_logins table for tracking student login events
CREATE TABLE IF NOT EXISTS student_logins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    login_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create index for efficient queries by student and date
CREATE INDEX idx_student_logins_student_date ON student_logins(student_id, login_at DESC);

-- Create index for date-based queries
CREATE INDEX idx_student_logins_date ON student_logins(login_at DESC);

-- Add comment to table
COMMENT ON TABLE student_logins IS 'Tracks student login events for analytics';
COMMENT ON COLUMN student_logins.student_id IS 'References students.id (foreign key will be added when students table exists)';
COMMENT ON COLUMN student_logins.login_at IS 'Timestamp when the student logged in';
COMMENT ON COLUMN student_logins.ip_address IS 'IP address of the login';
COMMENT ON COLUMN student_logins.user_agent IS 'User agent string from the browser';
