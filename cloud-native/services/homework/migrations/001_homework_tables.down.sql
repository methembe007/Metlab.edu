-- Rollback migration for homework service tables

BEGIN;

-- Drop service-specific indexes
DROP INDEX IF EXISTS idx_homework_assignments_teacher_due;
DROP INDEX IF EXISTS idx_homework_submissions_student;
DROP INDEX IF EXISTS idx_homework_grades_submission;
DROP INDEX IF EXISTS idx_homework_submissions_status;

-- Note: We don't drop the main tables as they are managed by infrastructure migrations
-- Only drop service-specific additions

COMMIT;
