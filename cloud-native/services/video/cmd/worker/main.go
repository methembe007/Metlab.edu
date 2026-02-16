package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strconv"
	"syscall"

	"github.com/metlab/video/internal/repository"
	"github.com/metlab/video/internal/worker"
	"github.com/redis/go-redis/v9"

	"github.com/metlab/shared/db"
	"github.com/metlab/shared/logger"
	"github.com/metlab/shared/queue"
	"github.com/metlab/shared/storage"
)

func main() {
	// Initialize logger
	logConfig := logger.DefaultConfig()
	logConfig.ServiceName = "video-worker"
	logr := logger.New(logConfig)

	// Get configuration from environment
	dbHost := getEnv("DB_HOST", "postgres-service")
	dbPort := getEnvInt("DB_PORT", 5432)
	dbUser := getEnv("DB_USER", "postgres")
	dbPassword := getEnv("DB_PASSWORD", "postgres")
	dbName := getEnv("DB_NAME", "metlab")

	redisHost := getEnv("REDIS_HOST", "redis-service")
	redisPort := getEnvInt("REDIS_PORT", 6379)
	redisPassword := getEnv("REDIS_PASSWORD", "")

	s3Endpoint := getEnv("S3_ENDPOINT", "http://minio-service:9000")
	s3AccessKey := getEnv("S3_ACCESS_KEY", "minioadmin")
	s3SecretKey := getEnv("S3_SECRET_KEY", "minioadmin123")
	videoBucket := getEnv("VIDEO_BUCKET", "metlab-videos")
	tempDir := getEnv("TEMP_DIR", "/tmp/video-processing")

	// Create temp directory if it doesn't exist
	if err := os.MkdirAll(tempDir, 0755); err != nil {
		logr.Fatal("failed to create temp directory", err)
	}

	// Initialize database connection
	dbConfig := &db.Config{
		Host:     dbHost,
		Port:     dbPort,
		User:     dbUser,
		Password: dbPassword,
		Database: dbName,
		SSLMode:  "disable",
		MinConns: 5,
		MaxConns: 20,
	}

	ctx := context.Background()
	dbPool, err := db.NewPool(ctx, dbConfig)
	if err != nil {
		logr.Fatal("failed to connect to database", err)
	}
	defer dbPool.Close()

	logr.Info("connected to database", map[string]interface{}{
		"host":     dbHost,
		"port":     dbPort,
		"database": dbName,
	})

	// Initialize storage client
	storageConfig := &storage.Config{
		Endpoint:        s3Endpoint,
		Region:          "us-east-1",
		AccessKeyID:     s3AccessKey,
		SecretAccessKey: s3SecretKey,
		UseSSL:          false,
		ForcePathStyle:  true,
	}

	storageClient, err := storage.NewClient(storageConfig)
	if err != nil {
		logr.Fatal("failed to create storage client", err)
	}

	logr.Info("connected to storage", map[string]interface{}{
		"endpoint": s3Endpoint,
		"bucket":   videoBucket,
	})

	// Initialize Redis client
	redisClient := redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%d", redisHost, redisPort),
		Password: redisPassword,
		DB:       0,
	})

	// Test Redis connection
	if err := redisClient.Ping(ctx).Err(); err != nil {
		logr.Fatal("failed to connect to Redis", err)
	}

	logr.Info("connected to Redis", map[string]interface{}{
		"host": redisHost,
		"port": redisPort,
	})

	// Initialize processing queue
	processingQueue := queue.NewQueue(redisClient, "video-processing")

	// Initialize repository
	videoRepo := repository.NewVideoRepository(dbPool)

	// Initialize video processor
	processor := worker.NewVideoProcessor(
		videoRepo,
		storageClient,
		processingQueue,
		videoBucket,
		tempDir,
		logr,
	)

	// Set up signal handling for graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	// Create context that can be cancelled
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start processor in a goroutine
	errChan := make(chan error, 1)
	go func() {
		errChan <- processor.Start(ctx)
	}()

	logr.Info("video worker started", map[string]interface{}{
		"temp_dir": tempDir,
	})

	// Wait for shutdown signal or error
	select {
	case sig := <-sigChan:
		logr.Info("received shutdown signal", map[string]interface{}{
			"signal": sig.String(),
		})
		cancel()
	case err := <-errChan:
		if err != nil && err != context.Canceled {
			logr.Error("worker error", err, nil)
			log.Fatal(err)
		}
	}

	logr.Info("video worker stopped", nil)
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}
