# Build stage
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git ca-certificates tzdata

WORKDIR /build

# Copy go mod files first for better caching
COPY services/analytics/go.mod services/analytics/go.sum ./services/analytics/
COPY shared/go.mod shared/go.sum ./shared/

# Download dependencies (cached layer)
WORKDIR /build/services/analytics
RUN go mod download && go mod verify

# Copy source code
WORKDIR /build
COPY services/analytics ./services/analytics
COPY shared ./shared
COPY proto ./proto

# Build with optimizations
WORKDIR /build/services/analytics
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a -installsuffix cgo \
    -o /app/analytics ./cmd/server

# Runtime stage - minimal image
FROM scratch

# Copy timezone data and certificates from builder
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group

# Copy binary
COPY --from=builder /app/analytics /analytics

# Use non-root user
USER nobody:nobody

EXPOSE 50054

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/analytics", "-health-check"]

ENTRYPOINT ["/analytics"]
