package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"time"
)

// Example: How to integrate Redis client in a microservice

// ServiceConfig holds service-specific Redis configuration
type ServiceConfig struct {
	RedisHost     string
	RedisPort     int
	RedisPassword string
	RedisDB       int
}

// LoadServiceConfigFromEnv loads Redis configuration from environment variables
func LoadServiceConfigFromEnv() *ServiceConfig {
	port := 6379
	if portStr := os.Getenv("REDIS_PORT"); portStr != "" {
		if p, err := strconv.Atoi(portStr); err == nil {
			port = p
		}
	}

	db := 0
	if dbStr := os.Getenv("REDIS_DB"); dbStr != "" {
		if d, err := strconv.Atoi(dbStr); err == nil {
			db = d
		}
	}

	return &ServiceConfig{
		RedisHost:     getEnvOrDefault("REDIS_HOST", "redis"),
		RedisPort:     port,
		RedisPassword: os.Getenv("REDIS_PASSWORD"),
		RedisDB:       db,
	}
}

func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// InitializeRedisClient creates a Redis client from environment configuration
func InitializeRedisClient(ctx context.Context) (*RedisClient, error) {
	svcCfg := LoadServiceConfigFromEnv()

	cfg := &RedisConfig{
		Host:               svcCfg.RedisHost,
		Port:               svcCfg.RedisPort,
		Password:           svcCfg.RedisPassword,
		DB:                 svcCfg.RedisDB,
		PoolSize:           100,
		MinIdleConns:       10,
		MaxConnAge:         time.Hour,
		PoolTimeout:        4 * time.Second,
		IdleTimeout:        5 * time.Minute,
		IdleCheckFrequency: time.Minute,
		DialTimeout:        5 * time.Second,
		ReadTimeout:        3 * time.Second,
		WriteTimeout:       3 * time.Second,
	}

	return NewRedisClient(ctx, cfg)
}

// CacheManager provides high-level caching operations
type CacheManager struct {
	client *RedisClient
}

// NewCacheManager creates a new cache manager
func NewCacheManager(client *RedisClient) *CacheManager {
	return &CacheManager{client: client}
}

// CacheJSON stores a JSON-serializable object in cache
func (cm *CacheManager) CacheJSON(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	data, err := json.Marshal(value)
	if err != nil {
		return fmt.Errorf("failed to marshal value: %w", err)
	}

	return cm.client.Set(ctx, key, data, ttl)
}

// GetJSON retrieves and unmarshals a JSON object from cache
func (cm *CacheManager) GetJSON(ctx context.Context, key string, dest interface{}) error {
	data, err := cm.client.Get(ctx, key)
	if err != nil {
		return err
	}

	if err := json.Unmarshal([]byte(data), dest); err != nil {
		return fmt.Errorf("failed to unmarshal value: %w", err)
	}

	return nil
}

// InvalidatePattern deletes all keys matching a pattern
func (cm *CacheManager) InvalidatePattern(ctx context.Context, pattern string) error {
	// Note: SCAN is preferred over KEYS in production for large datasets
	iter := cm.client.Client().Scan(ctx, 0, pattern, 0).Iterator()
	
	var keys []string
	for iter.Next(ctx) {
		keys = append(keys, iter.Val())
	}
	
	if err := iter.Err(); err != nil {
		return fmt.Errorf("failed to scan keys: %w", err)
	}

	if len(keys) > 0 {
		return cm.client.Del(ctx, keys...)
	}

	return nil
}

// SessionManager provides session management using Redis
type SessionManager struct {
	client *RedisClient
	prefix string
	ttl    time.Duration
}

// NewSessionManager creates a new session manager
func NewSessionManager(client *RedisClient, prefix string, ttl time.Duration) *SessionManager {
	return &SessionManager{
		client: client,
		prefix: prefix,
		ttl:    ttl,
	}
}

// CreateSession creates a new session
func (sm *SessionManager) CreateSession(ctx context.Context, sessionID string, data map[string]interface{}) error {
	key := fmt.Sprintf("%s:%s", sm.prefix, sessionID)
	
	// Convert map to slice for HSet
	var fields []interface{}
	for k, v := range data {
		fields = append(fields, k, v)
	}

	if err := sm.client.HSet(ctx, key, fields...); err != nil {
		return err
	}

	return sm.client.Expire(ctx, key, sm.ttl)
}

// GetSession retrieves session data
func (sm *SessionManager) GetSession(ctx context.Context, sessionID string) (map[string]string, error) {
	key := fmt.Sprintf("%s:%s", sm.prefix, sessionID)
	return sm.client.HGetAll(ctx, key)
}

// UpdateSession updates session data and refreshes TTL
func (sm *SessionManager) UpdateSession(ctx context.Context, sessionID string, data map[string]interface{}) error {
	key := fmt.Sprintf("%s:%s", sm.prefix, sessionID)
	
	var fields []interface{}
	for k, v := range data {
		fields = append(fields, k, v)
	}

	if err := sm.client.HSet(ctx, key, fields...); err != nil {
		return err
	}

	return sm.client.Expire(ctx, key, sm.ttl)
}

// DeleteSession deletes a session
func (sm *SessionManager) DeleteSession(ctx context.Context, sessionID string) error {
	key := fmt.Sprintf("%s:%s", sm.prefix, sessionID)
	return sm.client.Del(ctx, key)
}

// RateLimiter provides rate limiting functionality
type RateLimiter struct {
	client *RedisClient
	prefix string
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter(client *RedisClient, prefix string) *RateLimiter {
	return &RateLimiter{
		client: client,
		prefix: prefix,
	}
}

// CheckLimit checks if the rate limit has been exceeded
func (rl *RateLimiter) CheckLimit(ctx context.Context, identifier string, limit int64, window time.Duration) (bool, error) {
	key := fmt.Sprintf("%s:%s", rl.prefix, identifier)
	
	count, err := rl.client.Incr(ctx, key)
	if err != nil {
		return false, err
	}

	if count == 1 {
		// First request, set expiration
		if err := rl.client.Expire(ctx, key, window); err != nil {
			return false, err
		}
	}

	return count <= limit, nil
}

// GetRemainingRequests returns the number of remaining requests
func (rl *RateLimiter) GetRemainingRequests(ctx context.Context, identifier string, limit int64) (int64, error) {
	key := fmt.Sprintf("%s:%s", rl.prefix, identifier)
	
	count, err := rl.client.Get(ctx, key)
	if err != nil {
		// Key doesn't exist, all requests available
		return limit, nil
	}

	current, err := strconv.ParseInt(count, 10, 64)
	if err != nil {
		return 0, err
	}

	remaining := limit - current
	if remaining < 0 {
		remaining = 0
	}

	return remaining, nil
}

// PubSubManager provides pub/sub functionality for real-time features
type PubSubManager struct {
	client *RedisClient
}

// NewPubSubManager creates a new pub/sub manager
func NewPubSubManager(client *RedisClient) *PubSubManager {
	return &PubSubManager{client: client}
}

// PublishMessage publishes a message to a channel
func (pm *PubSubManager) PublishMessage(ctx context.Context, channel string, message interface{}) error {
	data, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("failed to marshal message: %w", err)
	}

	return pm.client.Publish(ctx, channel, data)
}

// SubscribeToChannel subscribes to a channel and processes messages
func (pm *PubSubManager) SubscribeToChannel(ctx context.Context, channel string, handler func([]byte) error) error {
	pubsub := pm.client.Subscribe(ctx, channel)
	defer pubsub.Close()

	// Wait for subscription confirmation
	_, err := pubsub.Receive(ctx)
	if err != nil {
		return fmt.Errorf("failed to receive subscription confirmation: %w", err)
	}

	// Process messages
	ch := pubsub.Channel()
	for {
		select {
		case msg := <-ch:
			if err := handler([]byte(msg.Payload)); err != nil {
				// Log error but continue processing
				fmt.Printf("Error handling message: %v\n", err)
			}
		case <-ctx.Done():
			return ctx.Err()
		}
	}
}

// Example usage in a service:
/*
func main() {
	ctx := context.Background()

	// Initialize Redis client
	redisClient, err := cache.InitializeRedisClient(ctx)
	if err != nil {
		log.Fatalf("Failed to initialize Redis: %v", err)
	}
	defer redisClient.Close()

	// Create cache manager
	cacheManager := cache.NewCacheManager(redisClient)

	// Cache some data
	user := User{ID: "123", Name: "John Doe"}
	err = cacheManager.CacheJSON(ctx, "user:123", user, 1*time.Hour)

	// Create session manager
	sessionManager := cache.NewSessionManager(redisClient, "session", 24*time.Hour)
	sessionManager.CreateSession(ctx, "abc123", map[string]interface{}{
		"user_id": "123",
		"role": "teacher",
	})

	// Create rate limiter
	rateLimiter := cache.NewRateLimiter(redisClient, "ratelimit")
	allowed, err := rateLimiter.CheckLimit(ctx, "192.168.1.1", 100, 1*time.Minute)
	if !allowed {
		log.Println("Rate limit exceeded")
	}

	// Create pub/sub manager for real-time chat
	pubsubManager := cache.NewPubSubManager(redisClient)
	
	// Publish message
	pubsubManager.PublishMessage(ctx, "chat:room1", map[string]string{
		"user": "John",
		"message": "Hello!",
	})

	// Subscribe to messages
	go pubsubManager.SubscribeToChannel(ctx, "chat:room1", func(data []byte) error {
		var msg map[string]string
		json.Unmarshal(data, &msg)
		log.Printf("Received: %v", msg)
		return nil
	})
}
*/
