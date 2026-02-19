-- Drop indexes
DROP INDEX IF EXISTS idx_pdf_downloads_date;
DROP INDEX IF EXISTS idx_pdf_downloads_pdf;
DROP INDEX IF EXISTS idx_pdf_downloads_student;

-- Drop table
DROP TABLE IF EXISTS pdf_downloads;
