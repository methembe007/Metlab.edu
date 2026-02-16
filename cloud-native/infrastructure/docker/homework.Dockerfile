# Build stage
FROM golang:1.24-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git ca-certificates tzdata

WORKDIR /build

# Copy go mod files first for better caching
COPY services/homework/go.mod services/homework/go.sum ./services/homework/
COPY shared/go.mod shared/go.sum ./shared/

# Download dependencies (cached layer)
WORKDIR /build/services/homework
RUN go mod download && go mod verify

# Copy source code
WORKDIR /build
COPY services/homework ./services/homework
COPY shared ./shared
COPY proto ./proto

# Build with optimizations
WORKDIR /build/services/homework
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a -installsuffix cgo \
    -o /app/homework ./cmd/server

# Runtime stage - minimal image
FROM scratch

# Copy timezone data and certificates from builder
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group

# Copy binary
COPY --from=builder /app/homework /homework

# Use non-root user
USER nobody:nobody

EXPOSE 50053

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/homework", "-health-check"]

ENTRYPOINT ["/homework"]
