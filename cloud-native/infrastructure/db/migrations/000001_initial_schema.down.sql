-- Rollback initial schema migration
-- This drops all tables in reverse order of dependencies

BEGIN;

-- Drop analytics tables
DROP TABLE IF EXISTS pdf_downloads CASCADE;
DROP TABLE IF EXISTS student_logins CASCADE;

-- Drop collaboration tables
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS chat_rooms CASCADE;
DROP TABLE IF EXISTS study_group_members CASCADE;
DROP TABLE IF EXISTS study_groups CASCADE;

-- Drop homework tables
DROP TABLE IF EXISTS homework_grades CASCADE;
DROP TABLE IF EXISTS homework_submissions CASCADE;
DROP TABLE IF EXISTS homework_assignments CASCADE;

-- Drop PDF tables
DROP TABLE IF EXISTS pdfs CASCADE;

-- Drop video tables
DROP TABLE IF EXISTS video_views CASCADE;
DROP TABLE IF EXISTS video_thumbnails CASCADE;
DROP TABLE IF EXISTS video_variants CASCADE;
DROP TABLE IF EXISTS videos CASCADE;

-- Drop student and class tables
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS signin_codes CASCADE;
DROP TABLE IF EXISTS classes CASCADE;

-- Drop teacher and user tables
DROP TABLE IF EXISTS teachers CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop extensions (optional - may be used by other databases)
-- DROP EXTENSION IF EXISTS "pgcrypto";
-- DROP EXTENSION IF EXISTS "uuid-ossp";

COMMIT;
