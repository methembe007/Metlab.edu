# Manual Testing Guide for Task 42: GetStudentLoginStats

## Prerequisites

1. PostgreSQL database running with analytics schema
2. Analytics service compiled and ready to run
3. grpcurl installed for testing (or use any gRPC client)

## Test Setup

### 1. Ensure Database is Running

```bash
# Check if PostgreSQL is running
psql -h localhost -U postgres -d metlab_analytics -c "SELECT 1"
```

### 2. Run Database Migrations

```bash
cd cloud-native/services/analytics
./scripts/run-migrations.sh
```

### 3. Insert Test Data

```sql
-- Connect to database
psql -h localhost -U postgres -d metlab_analytics

-- Insert test student logins
INSERT INTO student_logins (id, student_id, login_at, ip_address, user_agent) VALUES
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', NOW(), '192.168.1.1', 'Mozilla/5.0'),
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', NOW() - INTERVAL '1 day', '192.168.1.1', 'Mozilla/5.0'),
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', NOW() - INTERVAL '1 day', '192.168.1.1', 'Mozilla/5.0'),
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', NOW() - INTERVAL '2 days', '192.168.1.1', 'Mozilla/5.0'),
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', NOW() - INTERVAL '3 days', '192.168.1.1', 'Mozilla/5.0'),
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', NOW() - INTERVAL '3 days', '192.168.1.1', 'Mozilla/5.0'),
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', NOW() - INTERVAL '5 days', '192.168.1.1', 'Mozilla/5.0'),
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', NOW() - INTERVAL '7 days', '192.168.1.1', 'Mozilla/5.0'),
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', NOW() - INTERVAL '10 days', '192.168.1.1', 'Mozilla/5.0'),
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', NOW() - INTERVAL '15 days', '192.168.1.1', 'Mozilla/5.0');

-- Verify data
SELECT DATE(login_at) as date, COUNT(*) as count
FROM student_logins
WHERE student_id = '550e8400-e29b-41d4-a716-446655440000'
GROUP BY DATE(login_at)
ORDER BY date DESC;
```

Expected output:
```
    date    | count
------------+-------
 2026-02-19 |     1
 2026-02-18 |     2
 2026-02-17 |     1
 2026-02-16 |     2
 2026-02-14 |     1
 2026-02-12 |     1
 2026-02-09 |     1
 2026-02-04 |     1
```

## Test Execution

### 1. Start the Analytics Service

```bash
cd cloud-native/services/analytics
go run ./cmd/server
```

Expected output:
```
Successfully connected to database
Analytics service starting on port 50053
```

### 2. Test GetStudentLoginStats with grpcurl

#### Test Case 1: Default 30 days

```bash
grpcurl -plaintext -d '{
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "days": 30
}' localhost:50053 analytics.AnalyticsService/GetStudentLoginStats
```

Expected response:
```json
{
  "dailyCounts": [
    {
      "date": "2026-02-19",
      "count": 1
    },
    {
      "date": "2026-02-18",
      "count": 2
    },
    {
      "date": "2026-02-17",
      "count": 1
    },
    {
      "date": "2026-02-16",
      "count": 2
    },
    {
      "date": "2026-02-14",
      "count": 1
    },
    {
      "date": "2026-02-12",
      "count": 1
    },
    {
      "date": "2026-02-09",
      "count": 1
    },
    {
      "date": "2026-02-04",
      "count": 1
    }
  ],
  "totalLogins": 10,
  "averagePerWeek": 2.33
}
```

#### Test Case 2: Last 7 days only

```bash
grpcurl -plaintext -d '{
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "days": 7
}' localhost:50053 analytics.AnalyticsService/GetStudentLoginStats
```

Expected response:
```json
{
  "dailyCounts": [
    {
      "date": "2026-02-19",
      "count": 1
    },
    {
      "date": "2026-02-18",
      "count": 2
    },
    {
      "date": "2026-02-17",
      "count": 1
    },
    {
      "date": "2026-02-16",
      "count": 2
    },
    {
      "date": "2026-02-14",
      "count": 1
    }
  ],
  "totalLogins": 7,
  "averagePerWeek": 7.0
}
```

#### Test Case 3: Invalid student ID

```bash
grpcurl -plaintext -d '{
  "student_id": "invalid-uuid",
  "days": 30
}' localhost:50053 analytics.AnalyticsService/GetStudentLoginStats
```

Expected response:
```
ERROR:
  Code: InvalidArgument
  Message: invalid student_id format
```

#### Test Case 4: Missing student ID

```bash
grpcurl -plaintext -d '{
  "days": 30
}' localhost:50053 analytics.AnalyticsService/GetStudentLoginStats
```

Expected response:
```
ERROR:
  Code: InvalidArgument
  Message: student_id is required
```

#### Test Case 5: Student with no logins

```bash
grpcurl -plaintext -d '{
  "student_id": "00000000-0000-0000-0000-000000000000",
  "days": 30
}' localhost:50053 analytics.AnalyticsService/GetStudentLoginStats
```

Expected response:
```json
{
  "dailyCounts": [],
  "totalLogins": 0,
  "averagePerWeek": 0.0
}
```

## Verification Checklist

- [ ] Service starts without errors
- [ ] Database connection successful
- [ ] Test data inserted correctly
- [ ] GetStudentLoginStats returns daily counts
- [ ] Daily counts are aggregated correctly
- [ ] Total logins calculated correctly
- [ ] Average per week calculated correctly
- [ ] Data ordered by date descending
- [ ] Invalid UUID returns proper error
- [ ] Missing student_id returns proper error
- [ ] Student with no logins returns empty array
- [ ] Days parameter defaults to 30 when not specified

## Performance Test

### Test with Large Dataset

```sql
-- Insert 1000 login records over 30 days
DO $$
DECLARE
  i INTEGER;
BEGIN
  FOR i IN 1..1000 LOOP
    INSERT INTO student_logins (id, student_id, login_at, ip_address, user_agent)
    VALUES (
      gen_random_uuid(),
      '550e8400-e29b-41d4-a716-446655440000',
      NOW() - (random() * INTERVAL '30 days'),
      '192.168.1.1',
      'Mozilla/5.0'
    );
  END LOOP;
END $$;
```

Run the query and measure response time:
```bash
time grpcurl -plaintext -d '{
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "days": 30
}' localhost:50053 analytics.AnalyticsService/GetStudentLoginStats
```

Expected: Response time < 100ms

## Integration with API Gateway

Once the API Gateway is configured, test via HTTP:

```bash
# Assuming API Gateway is running on port 8080
curl -X GET "http://localhost:8080/api/analytics/students/550e8400-e29b-41d4-a716-446655440000/login-stats?days=30" \
  -H "Authorization: Bearer <jwt-token>"
```

## Cleanup

```sql
-- Remove test data
DELETE FROM student_logins WHERE student_id = '550e8400-e29b-41d4-a716-446655440000';
```

## Conclusion

If all test cases pass, Task 42 is successfully implemented and verified.
