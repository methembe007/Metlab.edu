# Build stage
FROM golang:1.21-alpine AS builder

# Install FFmpeg and build dependencies
RUN apk add --no-cache git ffmpeg

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
COPY ../../shared/go.mod ../../shared/go.sum ../../shared/

# Download dependencies
RUN go mod download

# Copy source code
COPY . .
COPY ../../shared ../../shared/

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o video-service ./cmd/server

# Runtime stage
FROM alpine:latest

# Install FFmpeg and FFprobe
RUN apk add --no-cache ffmpeg ca-certificates

WORKDIR /root/

# Copy the binary from builder
COPY --from=builder /app/video-service .

# Create temp directory for video processing
RUN mkdir -p /tmp/video-processing

# Expose gRPC port
EXPOSE 50052

# Run the service
CMD ["./video-service"]
