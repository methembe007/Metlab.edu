-- Migration for homework service tables
-- Note: These tables are already created in the main infrastructure schema
-- This migration file is for reference and service-specific migrations if needed

BEGIN;

-- Verify homework_assignments table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'homework_assignments') THEN
        RAISE EXCEPTION 'homework_assignments table does not exist. Run infrastructure migrations first.';
    END IF;
END $$;

-- Verify homework_submissions table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'homework_submissions') THEN
        RAISE EXCEPTION 'homework_submissions table does not exist. Run infrastructure migrations first.';
    END IF;
END $$;

-- Verify homework_grades table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'homework_grades') THEN
        RAISE EXCEPTION 'homework_grades table does not exist. Run infrastructure migrations first.';
    END IF;
END $$;

-- Add any service-specific indexes or constraints here
-- For example, additional indexes for performance optimization

-- Index for faster assignment lookups by teacher
CREATE INDEX IF NOT EXISTS idx_homework_assignments_teacher_due 
ON homework_assignments(teacher_id, due_date DESC);

-- Index for faster submission lookups by student
CREATE INDEX IF NOT EXISTS idx_homework_submissions_student 
ON homework_submissions(student_id, submitted_at DESC);

-- Index for faster grade lookups
CREATE INDEX IF NOT EXISTS idx_homework_grades_submission 
ON homework_grades(submission_id);

-- Index for filtering submissions by status
CREATE INDEX IF NOT EXISTS idx_homework_submissions_status 
ON homework_submissions(assignment_id, status);

COMMIT;
