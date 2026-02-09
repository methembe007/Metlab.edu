package db

import (
	"context"
	"os"
	"testing"
	"time"
)

func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()

	if cfg.Host != "localhost" {
		t.Errorf("Expected host to be localhost, got %s", cfg.Host)
	}

	if cfg.Port != 5432 {
		t.Errorf("Expected port to be 5432, got %d", cfg.Port)
	}

	if cfg.MinConns != 10 {
		t.Errorf("Expected MinConns to be 10, got %d", cfg.MinConns)
	}

	if cfg.MaxConns != 100 {
		t.Errorf("Expected MaxConns to be 100, got %d", cfg.MaxConns)
	}

	if cfg.MaxConnLifetime != time.Hour {
		t.Errorf("Expected MaxConnLifetime to be 1 hour, got %v", cfg.MaxConnLifetime)
	}
}

func TestNewPool(t *testing.T) {
	// Skip if no database is available
	if os.Getenv("DATABASE_URL") == "" {
		t.Skip("DATABASE_URL not set, skipping integration test")
	}

	ctx := context.Background()
	cfg := DefaultConfig()

	// Override with environment variables if set
	if host := os.Getenv("DB_HOST"); host != "" {
		cfg.Host = host
	}
	if password := os.Getenv("DB_PASSWORD"); password != "" {
		cfg.Password = password
	}

	pool, err := NewPool(ctx, cfg)
	if err != nil {
		t.Fatalf("Failed to create pool: %v", err)
	}
	defer pool.Close()

	// Test connection
	if err := pool.Ping(ctx); err != nil {
		t.Fatalf("Failed to ping database: %v", err)
	}

	// Test query
	var result int
	err = pool.QueryRow(ctx, "SELECT 1").Scan(&result)
	if err != nil {
		t.Fatalf("Failed to execute query: %v", err)
	}

	if result != 1 {
		t.Errorf("Expected result to be 1, got %d", result)
	}
}

func TestNewPoolFromURL(t *testing.T) {
	// Skip if no database is available
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		t.Skip("DATABASE_URL not set, skipping integration test")
	}

	ctx := context.Background()

	pool, err := NewPoolFromURL(ctx, dbURL)
	if err != nil {
		t.Fatalf("Failed to create pool from URL: %v", err)
	}
	defer pool.Close()

	// Test connection
	if err := pool.Ping(ctx); err != nil {
		t.Fatalf("Failed to ping database: %v", err)
	}

	// Verify pool configuration
	stats := pool.Stat()
	if stats.MaxConns() == 0 {
		t.Error("Expected MaxConns to be set")
	}
}

func TestGetPoolStats(t *testing.T) {
	// Skip if no database is available
	if os.Getenv("DATABASE_URL") == "" {
		t.Skip("DATABASE_URL not set, skipping integration test")
	}

	ctx := context.Background()
	cfg := DefaultConfig()

	pool, err := NewPool(ctx, cfg)
	if err != nil {
		t.Fatalf("Failed to create pool: %v", err)
	}
	defer pool.Close()

	// Get initial stats
	stats := GetPoolStats(pool)
	if stats == nil {
		t.Fatal("Expected stats to be non-nil")
	}

	// Verify stats structure
	if stats.MaxConns != cfg.MaxConns {
		t.Errorf("Expected MaxConns to be %d, got %d", cfg.MaxConns, stats.MaxConns)
	}

	// Acquire a connection and check stats
	conn, err := pool.Acquire(ctx)
	if err != nil {
		t.Fatalf("Failed to acquire connection: %v", err)
	}

	stats = GetPoolStats(pool)
	if stats.AcquiredConns == 0 {
		t.Error("Expected at least one acquired connection")
	}

	conn.Release()

	// Check stats after release
	stats = GetPoolStats(pool)
	if stats.IdleConns == 0 {
		t.Error("Expected at least one idle connection")
	}
}

func TestPoolConnectionLifecycle(t *testing.T) {
	// Skip if no database is available
	if os.Getenv("DATABASE_URL") == "" {
		t.Skip("DATABASE_URL not set, skipping integration test")
	}

	ctx := context.Background()
	cfg := DefaultConfig()
	cfg.MinConns = 2
	cfg.MaxConns = 5

	pool, err := NewPool(ctx, cfg)
	if err != nil {
		t.Fatalf("Failed to create pool: %v", err)
	}
	defer pool.Close()

	// Wait for min connections to be established
	time.Sleep(100 * time.Millisecond)

	stats := GetPoolStats(pool)
	if stats.TotalConns < cfg.MinConns {
		t.Errorf("Expected at least %d total connections, got %d", cfg.MinConns, stats.TotalConns)
	}

	// Acquire multiple connections
	conns := make([]interface{ Release() }, 0, 3)
	for i := 0; i < 3; i++ {
		conn, err := pool.Acquire(ctx)
		if err != nil {
			t.Fatalf("Failed to acquire connection %d: %v", i, err)
		}
		conns = append(conns, conn)
	}

	stats = GetPoolStats(pool)
	if stats.AcquiredConns != 3 {
		t.Errorf("Expected 3 acquired connections, got %d", stats.AcquiredConns)
	}

	// Release all connections
	for _, conn := range conns {
		conn.Release()
	}

	stats = GetPoolStats(pool)
	if stats.AcquiredConns != 0 {
		t.Errorf("Expected 0 acquired connections after release, got %d", stats.AcquiredConns)
	}
}
