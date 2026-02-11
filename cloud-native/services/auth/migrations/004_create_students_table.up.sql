-- Create students table
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    signin_code VARCHAR(8) REFERENCES signin_codes(code) ON DELETE SET NULL
);

-- Create index on teacher_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_students_teacher ON students(teacher_id);

-- Create index on signin_code
CREATE INDEX IF NOT EXISTS idx_students_signin_code ON students(signin_code);
