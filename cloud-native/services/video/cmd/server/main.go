package main

import (
	"context"
	"fmt"
	"net"
	"os"
	"strconv"

	"github.com/metlab/video/internal/repository"
	"github.com/metlab/video/internal/service"
	pb "github.com/metlab/shared/proto-gen/go/video"

	"github.com/metlab/shared/db"
	"github.com/metlab/shared/logger"
	"github.com/metlab/shared/queue"
	"github.com/metlab/shared/storage"
	"github.com/redis/go-redis/v9"

	"google.golang.org/grpc"
	"google.golang.org/grpc/health"
	"google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/reflection"
)

func main() {
	// Initialize logger
	logConfig := logger.DefaultConfig()
	logConfig.ServiceName = "video-service"
	log := logger.New(logConfig)

	// Get configuration from environment
	port := getEnv("PORT", "50052")
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
		log.Fatal("failed to create temp directory", err)
	}

	// Initialize database connection
	dbConfig := &db.Config{
		Host:     dbHost,
		Port:     dbPort,
		User:     dbUser,
		Password: dbPassword,
		Database: dbName,
		SSLMode:  "disable",
		MinConns: 10,
		MaxConns: 100,
	}

	ctx := context.Background()
	dbPool, err := db.NewPool(ctx, dbConfig)
	if err != nil {
		log.Fatal("failed to connect to database", err)
	}
	defer dbPool.Close()

	log.Info("connected to database", map[string]interface{}{
		"host": dbHost,
		"port": dbPort,
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
		log.Fatal("failed to create storage client", err)
	}

	log.Info("connected to storage", map[string]interface{}{
		"endpoint": s3Endpoint,
		"bucket": videoBucket,
	})

	// Ensure video bucket exists
	exists, err := storageClient.BucketExists(ctx, videoBucket)
	if err != nil {
		log.Fatal("failed to check bucket existence", err)
	}
	if !exists {
		if err := storageClient.CreateBucket(ctx, videoBucket); err != nil {
			log.Fatal("failed to create video bucket", err)
		}
		log.Info("created video bucket", map[string]interface{}{
			"bucket": videoBucket,
		})
	}

	// Initialize Redis client
	redisClient := redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%d", redisHost, redisPort),
		Password: redisPassword,
		DB:       0,
	})

	// Test Redis connection
	if err := redisClient.Ping(ctx).Err(); err != nil {
		log.Fatal("failed to connect to Redis", err)
	}

	log.Info("connected to Redis", map[string]interface{}{
		"host": redisHost,
		"port": redisPort,
	})

	// Initialize processing queue
	processingQueue := queue.NewQueue(redisClient, "video-processing")

	// Initialize repository
	videoRepo := repository.NewVideoRepository(dbPool)

	// Initialize video service
	videoService := service.NewVideoService(videoRepo, storageClient, processingQueue, videoBucket, tempDir)

	// Create gRPC server
	lis, err := net.Listen("tcp", fmt.Sprintf(":%s", port))
	if err != nil {
		log.Fatal("failed to listen", err)
	}

	grpcServer := grpc.NewServer()

	// Register video service
	pb.RegisterVideoServiceServer(grpcServer, videoService)

	// Register health check service
	healthServer := health.NewServer()
	grpc_health_v1.RegisterHealthServer(grpcServer, healthServer)
	healthServer.SetServingStatus("", grpc_health_v1.HealthCheckResponse_SERVING)

	// Register reflection service for development
	reflection.Register(grpcServer)

	log.Info("video service starting", map[string]interface{}{
		"port": port,
	})

	if err := grpcServer.Serve(lis); err != nil {
		log.Fatal("failed to serve", err)
	}
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
