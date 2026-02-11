package cache

import (
	"context"
	"testing"
	"time"
)

func TestDefaultRedisConfig(t *testing.T) {
	cfg := DefaultRedisConfig()
	
	if cfg.Host != "localhost" {
		t.Errorf("expected host to be localhost, got %s", cfg.Host)
	}
	
	if cfg.Port != 6379 {
		t.Errorf("expected port to be 6379, got %d", cfg.Port)
	}
	
	if cfg.PoolSize != 100 {
		t.Errorf("expected pool size to be 100, got %d", cfg.PoolSize)
	}
	
	if cfg.MinIdleConns != 10 {
		t.Errorf("expected min idle conns to be 10, got %d", cfg.MinIdleConns)
	}
}

func TestNewRedisClient(t *testing.T) {
	// Skip if Redis is not available
	cfg := DefaultRedisConfig()
	ctx := context.Background()
	
	client, err := NewRedisClient(ctx, cfg)
	if err != nil {
		t.Skipf("Redis not available: %v", err)
	}
	defer client.Close()
	
	// Test ping
	if err := client.Ping(ctx); err != nil {
		t.Errorf("failed to ping Redis: %v", err)
	}
}

func TestRedisClientOperations(t *testing.T) {
	cfg := DefaultRedisConfig()
	ctx := context.Background()
	
	client, err := NewRedisClient(ctx, cfg)
	if err != nil {
		t.Skipf("Redis not available: %v", err)
	}
	defer client.Close()
	
	// Test Set and Get
	key := "test:key"
	value := "test-value"
	
	if err := client.Set(ctx, key, value, time.Minute); err != nil {
		t.Fatalf("failed to set key: %v", err)
	}
	
	result, err := client.Get(ctx, key)
	if err != nil {
		t.Fatalf("failed to get key: %v", err)
	}
	
	if result != value {
		t.Errorf("expected value %s, got %s", value, result)
	}
	
	// Test Exists
	count, err := client.Exists(ctx, key)
	if err != nil {
		t.Fatalf("failed to check existence: %v", err)
	}
	
	if count != 1 {
		t.Errorf("expected key to exist, got count %d", count)
	}
	
	// Test Del
	if err := client.Del(ctx, key); err != nil {
		t.Fatalf("failed to delete key: %v", err)
	}
	
	count, err = client.Exists(ctx, key)
	if err != nil {
		t.Fatalf("failed to check existence after delete: %v", err)
	}
	
	if count != 0 {
		t.Errorf("expected key to not exist, got count %d", count)
	}
}

func TestRedisClientIncr(t *testing.T) {
	cfg := DefaultRedisConfig()
	ctx := context.Background()
	
	client, err := NewRedisClient(ctx, cfg)
	if err != nil {
		t.Skipf("Redis not available: %v", err)
	}
	defer client.Close()
	
	key := "test:counter"
	defer client.Del(ctx, key)
	
	// Test Incr
	val, err := client.Incr(ctx, key)
	if err != nil {
		t.Fatalf("failed to increment: %v", err)
	}
	
	if val != 1 {
		t.Errorf("expected value 1, got %d", val)
	}
	
	val, err = client.Incr(ctx, key)
	if err != nil {
		t.Fatalf("failed to increment: %v", err)
	}
	
	if val != 2 {
		t.Errorf("expected value 2, got %d", val)
	}
	
	// Test Decr
	val, err = client.Decr(ctx, key)
	if err != nil {
		t.Fatalf("failed to decrement: %v", err)
	}
	
	if val != 1 {
		t.Errorf("expected value 1, got %d", val)
	}
}

func TestRedisClientHash(t *testing.T) {
	cfg := DefaultRedisConfig()
	ctx := context.Background()
	
	client, err := NewRedisClient(ctx, cfg)
	if err != nil {
		t.Skipf("Redis not available: %v", err)
	}
	defer client.Close()
	
	key := "test:hash"
	defer client.Del(ctx, key)
	
	// Test HSet
	if err := client.HSet(ctx, key, "field1", "value1", "field2", "value2"); err != nil {
		t.Fatalf("failed to set hash: %v", err)
	}
	
	// Test HGet
	val, err := client.HGet(ctx, key, "field1")
	if err != nil {
		t.Fatalf("failed to get hash field: %v", err)
	}
	
	if val != "value1" {
		t.Errorf("expected value1, got %s", val)
	}
	
	// Test HGetAll
	all, err := client.HGetAll(ctx, key)
	if err != nil {
		t.Fatalf("failed to get all hash fields: %v", err)
	}
	
	if len(all) != 2 {
		t.Errorf("expected 2 fields, got %d", len(all))
	}
	
	if all["field1"] != "value1" || all["field2"] != "value2" {
		t.Errorf("unexpected hash values: %v", all)
	}
	
	// Test HDel
	if err := client.HDel(ctx, key, "field1"); err != nil {
		t.Fatalf("failed to delete hash field: %v", err)
	}
	
	all, err = client.HGetAll(ctx, key)
	if err != nil {
		t.Fatalf("failed to get all hash fields after delete: %v", err)
	}
	
	if len(all) != 1 {
		t.Errorf("expected 1 field after delete, got %d", len(all))
	}
}

func TestRedisClientPubSub(t *testing.T) {
	cfg := DefaultRedisConfig()
	ctx := context.Background()
	
	client, err := NewRedisClient(ctx, cfg)
	if err != nil {
		t.Skipf("Redis not available: %v", err)
	}
	defer client.Close()
	
	channel := "test:channel"
	message := "test-message"
	
	// Subscribe to channel
	pubsub := client.Subscribe(ctx, channel)
	defer pubsub.Close()
	
	// Wait for subscription to be ready
	_, err = pubsub.Receive(ctx)
	if err != nil {
		t.Fatalf("failed to receive subscription confirmation: %v", err)
	}
	
	// Publish message
	if err := client.Publish(ctx, channel, message); err != nil {
		t.Fatalf("failed to publish message: %v", err)
	}
	
	// Receive message
	msg, err := pubsub.ReceiveMessage(ctx)
	if err != nil {
		t.Fatalf("failed to receive message: %v", err)
	}
	
	if msg.Payload != message {
		t.Errorf("expected message %s, got %s", message, msg.Payload)
	}
}

func TestGetPoolStats(t *testing.T) {
	cfg := DefaultRedisConfig()
	ctx := context.Background()
	
	client, err := NewRedisClient(ctx, cfg)
	if err != nil {
		t.Skipf("Redis not available: %v", err)
	}
	defer client.Close()
	
	// Perform some operations to generate stats
	client.Set(ctx, "test:stats", "value", time.Minute)
	client.Get(ctx, "test:stats")
	client.Del(ctx, "test:stats")
	
	stats := client.GetPoolStats()
	if stats == nil {
		t.Error("expected pool stats, got nil")
	}
	
	// Stats should show some activity
	if stats.Hits == 0 && stats.Misses == 0 {
		t.Log("Warning: no pool activity recorded in stats")
	}
}
