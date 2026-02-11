-- Drop indexes
DROP INDEX IF EXISTS idx_signin_codes_used;
DROP INDEX IF EXISTS idx_signin_codes_expires;
DROP INDEX IF EXISTS idx_signin_codes_teacher;

-- Drop signin_codes table
DROP TABLE IF EXISTS signin_codes;

-- Drop classes indexes
DROP INDEX IF EXISTS idx_classes_teacher;

-- Drop classes table
DROP TABLE IF EXISTS classes;
