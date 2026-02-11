-- Create teachers table
CREATE TABLE IF NOT EXISTS teachers (
    id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    subject_area VARCHAR(100),
    verified BOOLEAN DEFAULT false
);

-- Create index on verified status
CREATE INDEX IF NOT EXISTS idx_teachers_verified ON teachers(verified);
