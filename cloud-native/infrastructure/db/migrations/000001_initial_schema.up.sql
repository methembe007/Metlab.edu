-- Initial schema migration for Metlab platform
-- This creates all core tables for the application

BEGIN;

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table (base for both teachers and students)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('teacher', 'student')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Teachers table
CREATE TABLE teachers (
    id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    subject_area VARCHAR(100),
    verified BOOLEAN DEFAULT false
);

-- Classes table
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(100),
    grade_level VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Signin codes for student registration
CREATE TABLE signin_codes (
    code VARCHAR(8) PRIMARY KEY,
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT false,
    used_by UUID REFERENCES users(id),
    used_at TIMESTAMP
);

-- Students table
CREATE TABLE students (
    id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    signin_code VARCHAR(8) REFERENCES signin_codes(code)
);

-- Videos table
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    original_filename VARCHAR(255),
    storage_path VARCHAR(500),
    duration_seconds INT,
    file_size_bytes BIGINT,
    status VARCHAR(20) CHECK (status IN ('uploading', 'processing', 'ready', 'failed')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Video variants for adaptive streaming
CREATE TABLE video_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    resolution VARCHAR(20),
    bitrate_kbps INT,
    storage_path VARCHAR(500),
    file_size_bytes BIGINT
);

-- Video thumbnails
CREATE TABLE video_thumbnails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    timestamp_percent INT,
    storage_path VARCHAR(500)
);

-- Video views tracking
CREATE TABLE video_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT NOW(),
    last_position_seconds INT DEFAULT 0,
    total_watch_seconds INT DEFAULT 0,
    completed BOOLEAN DEFAULT false,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(video_id, student_id)
);

-- PDFs table
CREATE TABLE pdfs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_name VARCHAR(255),
    storage_path VARCHAR(500),
    file_size_bytes BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Homework assignments
CREATE TABLE homework_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date TIMESTAMP NOT NULL,
    max_score INT DEFAULT 100,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Homework submissions
CREATE TABLE homework_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID REFERENCES homework_assignments(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    file_path VARCHAR(500),
    file_name VARCHAR(255),
    file_size_bytes BIGINT,
    submitted_at TIMESTAMP DEFAULT NOW(),
    is_late BOOLEAN DEFAULT false,
    status VARCHAR(20) CHECK (status IN ('submitted', 'graded', 'returned')),
    UNIQUE(assignment_id, student_id)
);

-- Homework grades
CREATE TABLE homework_grades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID REFERENCES homework_submissions(id) ON DELETE CASCADE UNIQUE,
    score INT,
    feedback TEXT,
    graded_by UUID REFERENCES teachers(id),
    graded_at TIMESTAMP DEFAULT NOW()
);

-- Study groups
CREATE TABLE study_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES students(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    max_members INT DEFAULT 10
);

-- Study group members
CREATE TABLE study_group_members (
    study_group_id UUID REFERENCES study_groups(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (study_group_id, student_id)
);

-- Chat rooms
CREATE TABLE chat_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    created_by UUID REFERENCES students(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat messages
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_room_id UUID REFERENCES chat_rooms(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES students(id) ON DELETE CASCADE,
    message_text TEXT,
    image_path VARCHAR(500),
    sent_at TIMESTAMP DEFAULT NOW()
);

-- Student logins for analytics
CREATE TABLE student_logins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    login_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- PDF downloads for analytics
CREATE TABLE pdf_downloads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pdf_id UUID REFERENCES pdfs(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    downloaded_at TIMESTAMP DEFAULT NOW()
);

COMMIT;
