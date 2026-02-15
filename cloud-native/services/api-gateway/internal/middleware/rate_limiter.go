package middleware

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"sync"
	"time"

	"github.com/redis/go-redis/v9"
)

// RateLimiter defines the interface for rate limiting implementations
type RateLimiter interface {
	Allow(ctx context.Context, key string) (bool, *RateLimitInfo, error)
}

// RateLimitInfo contains information about the rate limit status
type RateLimitInfo struct {
	Limit     int           // Maximum requests allowed
	Remaining int           // Remaining requests in current window
	Reset     time.Time     // When the rate limit resets
	RetryAfter time.Duration // How long to wait before retrying (if limited)
}

// InMemoryRateLimiter implements rate limiting using in-memory storage
type InMemoryRateLimiter struct {
	mu       sync.RWMutex
	requests map[string]*requestWindow
	limit    int
	window   time.Duration
}

type requestWindow struct {
	count     int
	resetTime time.Time
}

// NewInMemoryRateLimiter creates a new in-memory rate limiter
func NewInMemoryRateLimiter(limit int, window time.Duration) *InMemoryRateLimiter {
	limiter := &InMemoryRateLimiter{
		requests: make(map[string]*requestWindow),
		limit:    limit,
		window:   window,
	}

	// Start cleanup goroutine to remove expired entries
	go limiter.cleanup()

	return limiter
}

// Allow checks if a request is allowed for the given key
func (rl *InMemoryRateLimiter) Allow(ctx context.Context, key string) (bool, *RateLimitInfo, error) {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	window, exists := rl.requests[key]

	// Create new window if doesn't exist or expired
	if !exists || now.After(window.resetTime) {
		rl.requests[key] = &requestWindow{
			count:     1,
			resetTime: now.Add(rl.window),
		}
		return true, &RateLimitInfo{
			Limit:     rl.limit,
			Remaining: rl.limit - 1,
			Reset:     now.Add(rl.window),
		}, nil
	}

	// Check if limit exceeded
	if window.count >= rl.limit {
		retryAfter := time.Until(window.resetTime)
		return false, &RateLimitInfo{
			Limit:      rl.limit,
			Remaining:  0,
			Reset:      window.resetTime,
			RetryAfter: retryAfter,
		}, nil
	}

	// Increment counter
	window.count++
	return true, &RateLimitInfo{
		Limit:     rl.limit,
		Remaining: rl.limit - window.count,
		Reset:     window.resetTime,
	}, nil
}

// cleanup removes expired entries periodically
func (rl *InMemoryRateLimiter) cleanup() {
	ticker := time.NewTicker(time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		rl.mu.Lock()
		now := time.Now()
		for key, window := range rl.requests {
			if now.After(window.resetTime) {
				delete(rl.requests, key)
			}
		}
		rl.mu.Unlock()
	}
}

// RedisRateLimiter implements rate limiting using Redis
type RedisRateLimiter struct {
	client *redis.Client
	limit  int
	window time.Duration
}

// NewRedisRateLimiter creates a new Redis-backed rate limiter
func NewRedisRateLimiter(client *redis.Client, limit int, window time.Duration) *RedisRateLimiter {
	return &RedisRateLimiter{
		client: client,
		limit:  limit,
		window: window,
	}
}

// Allow checks if a request is allowed for the given key using Redis
func (rl *RedisRateLimiter) Allow(ctx context.Context, key string) (bool, *RateLimitInfo, error) {
	redisKey := fmt.Sprintf("rate_limit:%s", key)
	now := time.Now()

	// Use Redis pipeline for atomic operations
	pipe := rl.client.Pipeline()
	incrCmd := pipe.Incr(ctx, redisKey)
	ttlCmd := pipe.TTL(ctx, redisKey)
	_, err := pipe.Exec(ctx)

	if err != nil {
		return false, nil, fmt.Errorf("redis pipeline error: %w", err)
	}

	count := incrCmd.Val()
	ttl := ttlCmd.Val()

	// Set expiration if this is the first request in the window
	if count == 1 || ttl == -1 {
		if err := rl.client.Expire(ctx, redisKey, rl.window).Err(); err != nil {
			log.Printf("Failed to set expiration on rate limit key: %v", err)
		}
		ttl = rl.window
	}

	resetTime := now.Add(ttl)
	remaining := rl.limit - int(count)
	if remaining < 0 {
		remaining = 0
	}

	// Check if limit exceeded
	if count > int64(rl.limit) {
		return false, &RateLimitInfo{
			Limit:      rl.limit,
			Remaining:  0,
			Reset:      resetTime,
			RetryAfter: ttl,
		}, nil
	}

	return true, &RateLimitInfo{
		Limit:     rl.limit,
		Remaining: remaining,
		Reset:     resetTime,
	}, nil
}

// HybridRateLimiter uses in-memory limiter with Redis fallback
type HybridRateLimiter struct {
	memory *InMemoryRateLimiter
	redis  *RedisRateLimiter
}

// NewHybridRateLimiter creates a rate limiter that uses in-memory with Redis fallback
func NewHybridRateLimiter(redisClient *redis.Client, limit int, window time.Duration) *HybridRateLimiter {
	return &HybridRateLimiter{
		memory: NewInMemoryRateLimiter(limit, window),
		redis:  NewRedisRateLimiter(redisClient, limit, window),
	}
}

// Allow checks rate limit using in-memory first, falls back to Redis
func (hl *HybridRateLimiter) Allow(ctx context.Context, key string) (bool, *RateLimitInfo, error) {
	// Try Redis first for distributed rate limiting
	if hl.redis != nil {
		allowed, info, err := hl.redis.Allow(ctx, key)
		if err == nil {
			return allowed, info, nil
		}
		log.Printf("Redis rate limiter error, falling back to in-memory: %v", err)
	}

	// Fall back to in-memory
	return hl.memory.Allow(ctx, key)
}

// RateLimitConfig holds configuration for rate limiting middleware
type RateLimitConfig struct {
	Limit       int           // Maximum requests per window
	Window      time.Duration // Time window for rate limiting
	KeyFunc     func(*http.Request) string // Function to extract rate limit key
	RedisClient *redis.Client // Optional Redis client for distributed rate limiting
}

// DefaultRateLimitConfig returns default rate limit configuration
func DefaultRateLimitConfig() *RateLimitConfig {
	return &RateLimitConfig{
		Limit:  100,
		Window: time.Minute,
		KeyFunc: func(r *http.Request) string {
			// Use X-Forwarded-For if behind proxy, otherwise RemoteAddr
			if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
				return xff
			}
			return r.RemoteAddr
		},
	}
}

// RateLimit creates a rate limiting middleware
func RateLimit(config *RateLimitConfig) func(http.Handler) http.Handler {
	if config == nil {
		config = DefaultRateLimitConfig()
	}

	var limiter RateLimiter
	if config.RedisClient != nil {
		limiter = NewHybridRateLimiter(config.RedisClient, config.Limit, config.Window)
		log.Printf("Rate limiter initialized with Redis backing: %d requests per %v", config.Limit, config.Window)
	} else {
		limiter = NewInMemoryRateLimiter(config.Limit, config.Window)
		log.Printf("Rate limiter initialized (in-memory only): %d requests per %v", config.Limit, config.Window)
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Extract rate limit key (typically IP address)
			key := config.KeyFunc(r)

			// Check rate limit
			ctx := r.Context()
			allowed, info, err := limiter.Allow(ctx, key)

			if err != nil {
				log.Printf("Rate limiter error for key %s: %v", key, err)
				// On error, allow the request to proceed
				next.ServeHTTP(w, r)
				return
			}

			// Add rate limit headers to response
			w.Header().Set("X-RateLimit-Limit", strconv.Itoa(info.Limit))
			w.Header().Set("X-RateLimit-Remaining", strconv.Itoa(info.Remaining))
			w.Header().Set("X-RateLimit-Reset", strconv.FormatInt(info.Reset.Unix(), 10))

			if !allowed {
				// Rate limit exceeded
				w.Header().Set("Retry-After", strconv.Itoa(int(info.RetryAfter.Seconds())))
				log.Printf("Rate limit exceeded for key %s: %d/%d requests", key, info.Limit, info.Limit)
				
				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusTooManyRequests)
				w.Write([]byte(fmt.Sprintf(
					`{"error":"rate limit exceeded","message":"Too many requests. Please try again in %d seconds.","retry_after":%d}`,
					int(info.RetryAfter.Seconds()),
					int(info.RetryAfter.Seconds()),
				)))
				return
			}

			// Request allowed, continue to next handler
			next.ServeHTTP(w, r)
		})
	}
}
