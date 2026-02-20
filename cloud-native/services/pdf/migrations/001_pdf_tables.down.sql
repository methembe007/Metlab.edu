-- Rollback migration for PDF service tables

BEGIN;

-- Drop service-specific indexes
DROP INDEX IF EXISTS idx_pdfs_class_created;
DROP INDEX IF EXISTS idx_pdfs_teacher;
DROP INDEX IF EXISTS idx_pdf_downloads_student;
DROP INDEX IF EXISTS idx_pdf_downloads_pdf;

-- Note: We don't drop the main tables as they are managed by infrastructure migrations

COMMIT;
