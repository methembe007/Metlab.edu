-- Migration for PDF service tables
-- Note: These tables are already created in the main infrastructure schema
-- This migration file is for reference and service-specific migrations if needed

BEGIN;

-- Verify pdfs table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pdfs') THEN
        RAISE EXCEPTION 'pdfs table does not exist. Run infrastructure migrations first.';
    END IF;
END $$;

-- Verify pdf_downloads table exists (for analytics)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pdf_downloads') THEN
        RAISE EXCEPTION 'pdf_downloads table does not exist. Run infrastructure migrations first.';
    END IF;
END $$;

-- Add any service-specific indexes or constraints here
-- For example, additional indexes for performance optimization

-- Index for faster PDF lookups by class
CREATE INDEX IF NOT EXISTS idx_pdfs_class_created 
ON pdfs(class_id, created_at DESC);

-- Index for faster PDF lookups by teacher
CREATE INDEX IF NOT EXISTS idx_pdfs_teacher 
ON pdfs(teacher_id, created_at DESC);

-- Index for faster download tracking
CREATE INDEX IF NOT EXISTS idx_pdf_downloads_student 
ON pdf_downloads(student_id, downloaded_at DESC);

-- Index for PDF download analytics
CREATE INDEX IF NOT EXISTS idx_pdf_downloads_pdf 
ON pdf_downloads(pdf_id, downloaded_at DESC);

COMMIT;
