package middleware

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/alicebob/miniredis/v2"
	"github.com/redis/go-redis/v9"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestInMemoryRateLimiter(t *testing.T) {
	ctx := context.Background()
	limiter := NewInMemoryRateLimiter(3, time.Minute)

	t.Run("allows requests within limit", func(t *testing.T) {
		// First request
		allowed, info, err := limiter.Allow(ctx, "test-key")
		require.NoError(t, err)
		assert.True(t, allowed)
		assert.Equal(t, 3, info.Limit)
		assert.Equal(t, 2, info.Remaining)

		// Second request
		allowed, info, err = limiter.Allow(ctx, "test-key")
		require.NoError(t, err)
		assert.True(t, allowed)
		assert.Equal(t, 1, info.Remaining)

		// Third request
		allowed, info, err = limiter.Allow(ctx, "test-key")
		require.NoError(t, err)
		assert.True(t, allowed)
		assert.Equal(t, 0, info.Remaining)
	})

	t.Run("blocks requests exceeding limit", func(t *testing.T) {
		// Fourth request should be blocked
		allowed, info, err := limiter.Allow(ctx, "test-key")
		require.NoError(t, err)
		assert.False(t, allowed)
		assert.Equal(t, 0, info.Remaining)
		assert.Greater(t, info.RetryAfter, time.Duration(0))
	})

	t.Run("different keys have separate limits", func(t *testing.T) {
		allowed, info, err := limiter.Allow(ctx, "different-key")
		require.NoError(t, err)
		assert.True(t, allowed)
		assert.Equal(t, 2, info.Remaining)
	})

	t.Run("resets after window expires", func(t *testing.T) {
		limiter := NewInMemoryRateLimiter(2, 100*time.Millisecond)
		
		// Use up the limit
		limiter.Allow(ctx, "reset-key")
		limiter.Allow(ctx, "reset-key")
		
		// Should be blocked
		allowed, _, err := limiter.Allow(ctx, "reset-key")
		require.NoError(t, err)
		assert.False(t, allowed)
		
		// Wait for window to expire
		time.Sleep(150 * time.Millisecond)
		
		// Should be allowed again
		allowed, info, err := limiter.Allow(ctx, "reset-key")
		require.NoError(t, err)
		assert.True(t, allowed)
		assert.Equal(t, 1, info.Remaining)
	})
}

func TestRedisRateLimiter(t *testing.T) {
	// Start miniredis server
	mr, err := miniredis.Run()
	require.NoError(t, err)
	defer mr.Close()

	// Create Redis client
	client := redis.NewClient(&redis.Options{
		Addr: mr.Addr(),
	})
	defer client.Close()

	ctx := context.Background()
	limiter := NewRedisRateLimiter(client, 3, time.Minute)

	t.Run("allows requests within limit", func(t *testing.T) {
		// First request
		allowed, info, err := limiter.Allow(ctx, "test-key")
		require.NoError(t, err)
		assert.True(t, allowed)
		assert.Equal(t, 3, info.Limit)
		assert.Equal(t, 2, info.Remaining)

		// Second request
		allowed, info, err = limiter.Allow(ctx, "test-key")
		require.NoError(t, err)
		assert.True(t, allowed)
		assert.Equal(t, 1, info.Remaining)

		// Third request
		allowed, info, err = limiter.Allow(ctx, "test-key")
		require.NoError(t, err)
		assert.True(t, allowed)
		assert.Equal(t, 0, info.Remaining)
	})

	t.Run("blocks requests exceeding limit", func(t *testing.T) {
		// Fourth request should be blocked
		allowed, info, err := limiter.Allow(ctx, "test-key")
		require.NoError(t, err)
		assert.False(t, allowed)
		assert.Equal(t, 0, info.Remaining)
	})

	t.Run("different keys have separate limits", func(t *testing.T) {
		allowed, info, err := limiter.Allow(ctx, "different-key")
		require.NoError(t, err)
		assert.True(t, allowed)
		assert.Equal(t, 2, info.Remaining)
	})
}

func TestRateLimitMiddleware(t *testing.T) {
	// Create a test handler that just returns 200 OK
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	t.Run("allows requests within limit", func(t *testing.T) {
		config := &RateLimitConfig{
			Limit:  3,
			Window: time.Minute,
			KeyFunc: func(r *http.Request) string {
				return "test-ip"
			},
		}

		middleware := RateLimit(config)
		handler := middleware(testHandler)

		// First request
		req := httptest.NewRequest("GET", "/test", nil)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, req)
		assert.Equal(t, http.StatusOK, w.Code)
		assert.Equal(t, "3", w.Header().Get("X-RateLimit-Limit"))
		assert.Equal(t, "2", w.Header().Get("X-RateLimit-Remaining"))

		// Second request
		req = httptest.NewRequest("GET", "/test", nil)
		w = httptest.NewRecorder()
		handler.ServeHTTP(w, req)
		assert.Equal(t, http.StatusOK, w.Code)
		assert.Equal(t, "1", w.Header().Get("X-RateLimit-Remaining"))

		// Third request
		req = httptest.NewRequest("GET", "/test", nil)
		w = httptest.NewRecorder()
		handler.ServeHTTP(w, req)
		assert.Equal(t, http.StatusOK, w.Code)
		assert.Equal(t, "0", w.Header().Get("X-RateLimit-Remaining"))
	})

	t.Run("blocks requests exceeding limit", func(t *testing.T) {
		config := &RateLimitConfig{
			Limit:  2,
			Window: time.Minute,
			KeyFunc: func(r *http.Request) string {
				return "blocked-ip"
			},
		}

		middleware := RateLimit(config)
		handler := middleware(testHandler)

		// Use up the limit
		for i := 0; i < 2; i++ {
			req := httptest.NewRequest("GET", "/test", nil)
			w := httptest.NewRecorder()
			handler.ServeHTTP(w, req)
			assert.Equal(t, http.StatusOK, w.Code)
		}

		// Next request should be blocked
		req := httptest.NewRequest("GET", "/test", nil)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, req)
		assert.Equal(t, http.StatusTooManyRequests, w.Code)
		assert.Equal(t, "0", w.Header().Get("X-RateLimit-Remaining"))
		assert.NotEmpty(t, w.Header().Get("Retry-After"))
		assert.Contains(t, w.Body.String(), "rate limit exceeded")
	})

	t.Run("uses X-Forwarded-For header", func(t *testing.T) {
		config := &RateLimitConfig{
			Limit:  2,
			Window: time.Minute,
			KeyFunc: func(r *http.Request) string {
				if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
					return xff
				}
				return r.RemoteAddr
			},
		}

		middleware := RateLimit(config)
		handler := middleware(testHandler)

		// Requests from different IPs should have separate limits
		req1 := httptest.NewRequest("GET", "/test", nil)
		req1.Header.Set("X-Forwarded-For", "192.168.1.1")
		w1 := httptest.NewRecorder()
		handler.ServeHTTP(w1, req1)
		assert.Equal(t, http.StatusOK, w1.Code)

		req2 := httptest.NewRequest("GET", "/test", nil)
		req2.Header.Set("X-Forwarded-For", "192.168.1.2")
		w2 := httptest.NewRecorder()
		handler.ServeHTTP(w2, req2)
		assert.Equal(t, http.StatusOK, w2.Code)
		assert.Equal(t, "1", w2.Header().Get("X-RateLimit-Remaining"))
	})

	t.Run("uses default config when nil", func(t *testing.T) {
		middleware := RateLimit(nil)
		handler := middleware(testHandler)

		req := httptest.NewRequest("GET", "/test", nil)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, req)
		assert.Equal(t, http.StatusOK, w.Code)
		assert.Equal(t, "100", w.Header().Get("X-RateLimit-Limit"))
	})
}

func TestRateLimitMiddlewareWithRedis(t *testing.T) {
	// Start miniredis server
	mr, err := miniredis.Run()
	require.NoError(t, err)
	defer mr.Close()

	// Create Redis client
	client := redis.NewClient(&redis.Options{
		Addr: mr.Addr(),
	})
	defer client.Close()

	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	t.Run("uses Redis for distributed rate limiting", func(t *testing.T) {
		config := &RateLimitConfig{
			Limit:       3,
			Window:      time.Minute,
			RedisClient: client,
			KeyFunc: func(r *http.Request) string {
				return "redis-test-ip"
			},
		}

		middleware := RateLimit(config)
		handler := middleware(testHandler)

		// Make requests
		for i := 0; i < 3; i++ {
			req := httptest.NewRequest("GET", "/test", nil)
			w := httptest.NewRecorder()
			handler.ServeHTTP(w, req)
			assert.Equal(t, http.StatusOK, w.Code)
		}

		// Fourth request should be blocked
		req := httptest.NewRequest("GET", "/test", nil)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, req)
		assert.Equal(t, http.StatusTooManyRequests, w.Code)
	})
}
