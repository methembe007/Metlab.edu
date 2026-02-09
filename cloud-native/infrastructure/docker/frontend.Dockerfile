# Build stage
FROM node:20-alpine AS builder

# Install build dependencies
RUN apk add --no-cache python3 make g++

WORKDIR /build

# Copy package files first for better caching
COPY frontend/package*.json ./

# Install dependencies with clean install
RUN npm ci --prefer-offline --no-audit

# Copy source code
COPY frontend/ ./

# Build application with optimizations
ENV NODE_ENV=production
RUN npm run build

# Prune dev dependencies
RUN npm prune --production

# Runtime stage - minimal image
FROM node:20-alpine

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init && \
    addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

WORKDIR /app

# Copy built application and production dependencies
COPY --from=builder --chown=appuser:appuser /build/.output ./.output
COPY --from=builder --chown=appuser:appuser /build/node_modules ./node_modules
COPY --from=builder --chown=appuser:appuser /build/package*.json ./

# Use non-root user
USER appuser:appuser

EXPOSE 3000

ENV NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", ".output/server/index.mjs"]
