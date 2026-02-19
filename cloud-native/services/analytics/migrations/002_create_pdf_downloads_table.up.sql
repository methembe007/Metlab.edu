-- Create pdf_downloads table for tracking PDF download events
CREATE TABLE IF NOT EXISTS pdf_downloads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pdf_id UUID NOT NULL,
    student_id UUID NOT NULL,
    downloaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create index for efficient queries by student
CREATE INDEX idx_pdf_downloads_student ON pdf_downloads(student_id, downloaded_at DESC);

-- Create index for efficient queries by PDF
CREATE INDEX idx_pdf_downloads_pdf ON pdf_downloads(pdf_id, downloaded_at DESC);

-- Create index for date-based queries
CREATE INDEX idx_pdf_downloads_date ON pdf_downloads(downloaded_at DESC);

-- Add comment to table
COMMENT ON TABLE pdf_downloads IS 'Tracks PDF download events for analytics';
COMMENT ON COLUMN pdf_downloads.pdf_id IS 'References pdfs.id (foreign key will be added when pdfs table exists)';
COMMENT ON COLUMN pdf_downloads.student_id IS 'References students.id (foreign key will be added when students table exists)';
COMMENT ON COLUMN pdf_downloads.downloaded_at IS 'Timestamp when the PDF was downloaded';
