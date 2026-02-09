# Build stage
FROM golang:1.21-alpine AS builder

# Install build dependencies including FFmpeg for video processing
RUN apk add --no-cache git ca-certificates tzdata ffmpeg

WORKDIR /build

# Copy go mod files first for better caching
COPY services/video/go.mod services/video/go.sum ./services/video/
COPY shared/go.mod shared/go.sum ./shared/

# Download dependencies (cached layer)
WORKDIR /build/services/video
RUN go mod download && go mod verify

# Copy source code
WORKDIR /build
COPY services/video ./services/video
COPY shared ./shared
COPY proto ./proto

# Build with optimizations
WORKDIR /build/services/video
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a -installsuffix cgo \
    -o /app/video ./cmd/server

# Runtime stage - alpine for FFmpeg support
FROM alpine:latest

# Install runtime dependencies
RUN apk add --no-cache ca-certificates tzdata ffmpeg && \
    addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

WORKDIR /app

# Copy binary
COPY --from=builder /app/video .

# Create temp directory for video processing
RUN mkdir -p /tmp/video-processing && \
    chown -R appuser:appuser /tmp/video-processing /app

# Use non-root user
USER appuser:appuser

EXPOSE 50052

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/app/video", "-health-check"]

ENTRYPOINT ["/app/video"]
