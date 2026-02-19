# Collaboration Service

The Collaboration Service handles study groups and real-time chat functionality for the Metlab.edu platform.

## Features

### Study Groups
- Create study groups within a class
- Join existing study groups
- List available study groups
- Enforce business rules:
  - Maximum 10 members per group
  - Students can join up to 5 groups
  - Groups restricted to same class

### Chat Rooms
- Create chat rooms for class discussions
- Send text messages (up to 1000 characters)
- Send image attachments (up to 5MB)
- Real-time message streaming via gRPC
- Message history retrieval (7-day retention)
- Redis pub/sub for real-time delivery

## Architecture

### Components

- **gRPC Server**: Handles all collaboration requests
- **PostgreSQL**: Stores study groups, chat rooms, and messages
- **Redis**: Pub/sub for real-time message delivery
- **S3 Storage**: Stores chat image attachments (future implementation)

### Database Schema

#### study_groups
- Stores study group information
- Enforces max_members constraint

#### study_group_members
- Many-to-many relationship between groups and students
- Tracks join timestamps

#### chat_rooms
- Stores chat room information
- Associated with a class

#### chat_messages
- Stores chat messages
- Supports text and image content
- Indexed for efficient retrieval

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Environment Variables

- `PORT`: gRPC server port (default: 50055)
- `DATABASE_*`: PostgreSQL connection settings
- `REDIS_*`: Redis connection settings
- `S3_*`: S3 storage settings for images
- `MAX_GROUP_MEMBERS`: Maximum members per group (default: 10)
- `MAX_GROUPS_PER_STUDENT`: Maximum groups per student (default: 5)
- `MESSAGE_RETENTION_DAYS`: Message retention period (default: 7)
- `MAX_MESSAGE_LENGTH`: Maximum message text length (default: 1000)
- `MAX_IMAGE_SIZE_MB`: Maximum image size (default: 5)

## Development

### Prerequisites

- Go 1.21+
- PostgreSQL 15+
- Redis 7+
- Protocol Buffers compiler

### Setup

1. Install dependencies:
```bash
make deps
```

2. Run database migrations:
```bash
export DATABASE_URL="postgres://user:pass@localhost:5432/metlab?sslmode=disable"
make migrate-up
```

3. Run the service:
```bash
make run
```

### Building

```bash
make build
```

### Testing

```bash
make test
```

### Docker

Build Docker image:
```bash
make docker-build
```

Run Docker container:
```bash
make docker-run
```

## API

### gRPC Methods

#### Study Groups

- `CreateStudyGroup`: Create a new study group
- `JoinStudyGroup`: Join an existing study group
- `ListStudyGroups`: List all study groups for a class

#### Chat

- `CreateChatRoom`: Create a new chat room
- `SendMessage`: Send a message to a chat room
- `GetMessages`: Retrieve message history
- `StreamMessages`: Stream real-time messages (server streaming)

## Redis Pub/Sub

Messages are published to Redis channels for real-time delivery:

- Channel format: `chat:room:{room_id}`
- Message format: JSON-serialized ChatMessage

## Background Jobs

### Message Cleanup

Runs daily to delete messages older than the retention period (default: 7 days).

## Monitoring

### Health Checks

The service exposes gRPC health check endpoints:

```bash
grpcurl -plaintext localhost:50055 grpc.health.v1.Health/Check
```

### Logging

All requests are logged with:
- Method name
- Duration
- Success/error status

## Migration

### Creating New Migrations

```bash
make migrate-create
# Enter migration name when prompted
```

### Running Migrations

Up:
```bash
make migrate-up
```

Down:
```bash
make migrate-down
```

## Future Enhancements

- [ ] Implement S3 image upload for chat attachments
- [ ] Add message editing and deletion
- [ ] Add typing indicators
- [ ] Add read receipts
- [ ] Add message reactions
- [ ] Add file attachments (PDFs, documents)
- [ ] Add voice messages
- [ ] Add video calls integration
- [ ] Add study group announcements
- [ ] Add study group scheduling
