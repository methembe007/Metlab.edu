-- Create classes table (needed for signin_codes foreign key)
CREATE TABLE IF NOT EXISTS classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(100),
    grade_level VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Create index on teacher_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_classes_teacher ON classes(teacher_id);

-- Create signin_codes table
CREATE TABLE IF NOT EXISTS signin_codes (
    code VARCHAR(8) PRIMARY KEY,
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT false,
    used_by UUID REFERENCES users(id) ON DELETE SET NULL,
    used_at TIMESTAMP
);

-- Create index on teacher_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_signin_codes_teacher ON signin_codes(teacher_id);

-- Create index on expires_at for cleanup and validation
CREATE INDEX IF NOT EXISTS idx_signin_codes_expires ON signin_codes(expires_at) WHERE NOT used;

-- Create index on used status
CREATE INDEX IF NOT EXISTS idx_signin_codes_used ON signin_codes(used);
