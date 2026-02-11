# Authentication Service

The Authentication Service handles user authentication, authorization, and session management for the Metlab.edu platform.

## Features

- Teacher registration and login with email/password
- Student signin with teacher name, student name, and signin code
- JWT token generation and validation
- Account lockout after failed login attempts
- Signin code generation for student registration

## Project Structure

```
auth/
├── cmd/
│   └── server/
│       └── main.go              # Application entry point
├── internal/
│   ├── config/
│   │   └── config.go            # Configuration management
│   ├── db/
│   │   └── db.go                # Database connection pool
│   ├── models/
│   │   └── user.go              # Data models
│   ├── repository/
│   │   ├── user_repository.go
│   │   ├── teacher_repository.go
│   │   ├── student_repository.go
│   │   ├── signin_code_repository.go
│   │   └── login_attempt_repository.go
│   ├── service/
│   │   └── auth_service.go      # Business logic
│   └── utils/
│       ├── jwt.go               # JWT utilities
│       ├── password.go          # Password validation
│       └── code_generator.go    # Signin code generation
├── migrations/
│   ├── 001_create_users_table.up.sql
│   ├── 001_create_users_table.down.sql
│   ├── 002_create_teachers_table.up.sql
│   ├── 002_create_teachers_table.down.sql
│   ├── 003_create_signin_codes_table.up.sql
│   ├── 003_create_signin_codes_table.down.sql
│   ├── 004_create_students_table.up.sql
│   ├── 004_create_students_table.down.sql
│   ├── 005_create_login_attempts_table.up.sql
│   └── 005_create_login_attempts_table.down.sql
├── go.mod
├── go.sum
├── Dockerfile
└── README.md
```

## Database Schema

### Users Table
- Stores all users (teachers and students)
- Email and password for teachers
- Role-based access control

### Teachers Table
- Extended information for teacher users
- Subject area and verification status

### Students Table
- Extended information for student users
- Links to teacher and signin code

### Signin Codes Table
- Unique codes for student registration
- 30-day expiration
- One-time use

### Login Attempts Table
- Tracks login attempts for security
- Enables account lockout after failed attempts

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| PORT | gRPC server port | 50051 |
| DATABASE_HOST | PostgreSQL host | localhost |
| DATABASE_PORT | PostgreSQL port | 5432 |
| DATABASE_USER | PostgreSQL user | postgres |
| DATABASE_PASSWORD | PostgreSQL password | postgres |
| DATABASE_NAME | PostgreSQL database name | metlab |
| JWT_SECRET | Secret key for JWT signing | dev-secret-change-in-production |
| JWT_EXPIRY_HOURS | JWT token expiry in hours | 24 |
| STUDENT_EXPIRY_DAYS | Student JWT expiry in days | 7 |
| MAX_LOGIN_ATTEMPTS | Max failed login attempts | 5 |
| LOCKOUT_MINUTES | Account lockout duration | 30 |

## Running the Service

### Prerequisites
- Go 1.21+
- PostgreSQL 15+
- Protocol Buffers compiler (protoc)

### Local Development

1. Install dependencies:
```bash
go mod download
```

2. Run database migrations:
```bash
# Use golang-migrate or your preferred migration tool
migrate -path migrations -database "postgres://postgres:postgres@localhost:5432/metlab?sslmode=disable" up
```

3. Set environment variables:
```bash
export DATABASE_HOST=localhost
export DATABASE_PASSWORD=your_password
export JWT_SECRET=your_secret_key
```

4. Run the service:
```bash
go run cmd/server/main.go
```

### Docker

Build and run with Docker:
```bash
docker build -t metlab/auth:latest .
docker run -p 50051:50051 \
  -e DATABASE_HOST=postgres \
  -e DATABASE_PASSWORD=secret \
  -e JWT_SECRET=secret \
  metlab/auth:latest
```

## gRPC Service Definition

The service implements the following RPC methods (defined in `proto/auth/auth.proto`):

- `TeacherSignup`: Register a new teacher account
- `TeacherLogin`: Authenticate a teacher
- `StudentSignin`: Authenticate a student with signin code
- `ValidateToken`: Validate a JWT token
- `GenerateSigninCode`: Generate a signin code for student registration

## Security Features

- Password requirements: minimum 12 characters with uppercase, lowercase, numbers, and special characters
- Bcrypt password hashing with default cost
- JWT tokens with configurable expiry
- Account lockout after 5 failed login attempts within 15 minutes
- Prepared statements to prevent SQL injection
- Connection pooling with health checks

## Health Checks

The service exposes gRPC health check endpoints:
- Overall service health: `grpc.health.v1.Health/Check`
- Auth service health: `auth.AuthService`

## Next Steps

1. Generate gRPC code from proto definitions
2. Implement gRPC handler layer
3. Add student signin and signin code generation logic
4. Add comprehensive unit tests
5. Add integration tests with test database
6. Set up CI/CD pipeline
