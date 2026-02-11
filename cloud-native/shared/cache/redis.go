package cache

import (
	"context"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

// RedisConfig holds Redis configuration
type RedisConfig struct {
	Host     string
	Port     int
	Password string
	DB       int
	// Connection pool settings
	PoolSize           int
	MinIdleConns       int
	MaxConnAge         time.Duration
	PoolTimeout        time.Duration
	IdleTimeout        time.Duration
	IdleCheckFrequency time.Duration
	// Timeouts
	DialTimeout  time.Duration
	ReadTimeout  time.Duration
	WriteTimeout time.Duration
}

// DefaultRedisConfig returns a configuration with sensible defaults
func DefaultRedisConfig() *RedisConfig {
	return &RedisConfig{
		Host:               "localhost",
		Port:               6379,
		Password:           "",
		DB:                 0,
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
}

// RedisClient wraps the go-redis client with additional functionality
type RedisClient struct {
	client *redis.Client
	config *RedisConfig
}

// NewRedisClient creates a new Redis client with the given configuration
func NewRedisClient(ctx context.Context, cfg *RedisConfig) (*RedisClient, error) {
	if cfg == nil {
		cfg = DefaultRedisConfig()
	}

	client := redis.NewClient(&redis.Options{
		Addr:               fmt.Sprintf("%s:%d", cfg.Host, cfg.Port),
		Password:           cfg.Password,
		DB:                 cfg.DB,
		PoolSize:           cfg.PoolSize,
		MinIdleConns:       cfg.MinIdleConns,
		MaxConnAge:         cfg.MaxConnAge,
		PoolTimeout:        cfg.PoolTimeout,
		ConnMaxIdleTime:    cfg.IdleTimeout,
		DialTimeout:        cfg.DialTimeout,
		ReadTimeout:        cfg.ReadTimeout,
		WriteTimeout:       cfg.WriteTimeout,
	})

	// Verify connection
	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("failed to ping Redis: %w", err)
	}

	return &RedisClient{
		client: client,
		config: cfg,
	}, nil
}

// NewRedisClientFromURL creates a new Redis client from a connection URL
func NewRedisClientFromURL(ctx context.Context, url string) (*RedisClient, error) {
	opts, err := redis.ParseURL(url)
	if err != nil {
		return nil, fmt.Errorf("failed to parse Redis URL: %w", err)
	}

	// Set default pool configuration if not specified
	if opts.PoolSize == 0 {
		opts.PoolSize = 100
	}
	if opts.MinIdleConns == 0 {
		opts.MinIdleConns = 10
	}
	if opts.MaxConnAge == 0 {
		opts.MaxConnAge = time.Hour
	}
	if opts.PoolTimeout == 0 {
		opts.PoolTimeout = 4 * time.Second
	}
	if opts.ConnMaxIdleTime == 0 {
		opts.ConnMaxIdleTime = 5 * time.Minute
	}
	if opts.DialTimeout == 0 {
		opts.DialTimeout = 5 * time.Second
	}
	if opts.ReadTimeout == 0 {
		opts.ReadTimeout = 3 * time.Second
	}
	if opts.WriteTimeout == 0 {
		opts.WriteTimeout = 3 * time.Second
	}

	client := redis.NewClient(opts)

	// Verify connection
	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("failed to ping Redis: %w", err)
	}

	return &RedisClient{
		client: client,
		config: &RedisConfig{
			Host:               opts.Addr,
			Password:           opts.Password,
			DB:                 opts.DB,
			PoolSize:           opts.PoolSize,
			MinIdleConns:       opts.MinIdleConns,
			MaxConnAge:         opts.MaxConnAge,
			PoolTimeout:        opts.PoolTimeout,
			IdleTimeout:        opts.ConnMaxIdleTime,
			DialTimeout:        opts.DialTimeout,
			ReadTimeout:        opts.ReadTimeout,
			WriteTimeout:       opts.WriteTimeout,
		},
	}, nil
}

// Client returns the underlying go-redis client
func (rc *RedisClient) Client() *redis.Client {
	return rc.client
}

// Close closes the Redis connection
func (rc *RedisClient) Close() error {
	return rc.client.Close()
}

// Ping verifies the connection to Redis
func (rc *RedisClient) Ping(ctx context.Context) error {
	return rc.client.Ping(ctx).Err()
}

// Set stores a key-value pair with optional expiration
func (rc *RedisClient) Set(ctx context.Context, key string, value interface{}, expiration time.Duration) error {
	return rc.client.Set(ctx, key, value, expiration).Err()
}

// Get retrieves a value by key
func (rc *RedisClient) Get(ctx context.Context, key string) (string, error) {
	return rc.client.Get(ctx, key).Result()
}

// Del deletes one or more keys
func (rc *RedisClient) Del(ctx context.Context, keys ...string) error {
	return rc.client.Del(ctx, keys...).Err()
}

// Exists checks if one or more keys exist
func (rc *RedisClient) Exists(ctx context.Context, keys ...string) (int64, error) {
	return rc.client.Exists(ctx, keys...).Result()
}

// Expire sets an expiration time on a key
func (rc *RedisClient) Expire(ctx context.Context, key string, expiration time.Duration) error {
	return rc.client.Expire(ctx, key, expiration).Err()
}

// TTL returns the remaining time to live of a key
func (rc *RedisClient) TTL(ctx context.Context, key string) (time.Duration, error) {
	return rc.client.TTL(ctx, key).Result()
}

// Incr increments the integer value of a key by one
func (rc *RedisClient) Incr(ctx context.Context, key string) (int64, error) {
	return rc.client.Incr(ctx, key).Result()
}

// Decr decrements the integer value of a key by one
func (rc *RedisClient) Decr(ctx context.Context, key string) (int64, error) {
	return rc.client.Decr(ctx, key).Result()
}

// HSet sets field in the hash stored at key to value
func (rc *RedisClient) HSet(ctx context.Context, key string, values ...interface{}) error {
	return rc.client.HSet(ctx, key, values...).Err()
}

// HGet returns the value associated with field in the hash stored at key
func (rc *RedisClient) HGet(ctx context.Context, key, field string) (string, error) {
	return rc.client.HGet(ctx, key, field).Result()
}

// HGetAll returns all fields and values of the hash stored at key
func (rc *RedisClient) HGetAll(ctx context.Context, key string) (map[string]string, error) {
	return rc.client.HGetAll(ctx, key).Result()
}

// HDel deletes one or more hash fields
func (rc *RedisClient) HDel(ctx context.Context, key string, fields ...string) error {
	return rc.client.HDel(ctx, key, fields...).Err()
}

// Publish posts a message to a channel
func (rc *RedisClient) Publish(ctx context.Context, channel string, message interface{}) error {
	return rc.client.Publish(ctx, channel, message).Err()
}

// Subscribe subscribes to one or more channels
func (rc *RedisClient) Subscribe(ctx context.Context, channels ...string) *redis.PubSub {
	return rc.client.Subscribe(ctx, channels...)
}

// PSubscribe subscribes to channels matching a pattern
func (rc *RedisClient) PSubscribe(ctx context.Context, patterns ...string) *redis.PubSub {
	return rc.client.PSubscribe(ctx, patterns...)
}

// PoolStats returns statistics about the connection pool
type PoolStats struct {
	Hits     uint32
	Misses   uint32
	Timeouts uint32
	TotalConns uint32
	IdleConns  uint32
	StaleConns uint32
}

// GetPoolStats returns statistics about the Redis connection pool
func (rc *RedisClient) GetPoolStats() *PoolStats {
	stats := rc.client.PoolStats()
	return &PoolStats{
		Hits:       stats.Hits,
		Misses:     stats.Misses,
		Timeouts:   stats.Timeouts,
		TotalConns: stats.TotalConns,
		IdleConns:  stats.IdleConns,
		StaleConns: stats.StaleConns,
	}
}

// Pipeline creates a new pipeline for batching commands
func (rc *RedisClient) Pipeline() redis.Pipeliner {
	return rc.client.Pipeline()
}

// TxPipeline creates a new transaction pipeline
func (rc *RedisClient) TxPipeline() redis.Pipeliner {
	return rc.client.TxPipeline()
}
