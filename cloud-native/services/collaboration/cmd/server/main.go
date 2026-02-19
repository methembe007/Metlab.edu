package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/metlab/collaboration/internal/config"
	"github.com/metlab/collaboration/internal/db"
	"github.com/metlab/collaboration/internal/handler"
	"github.com/metlab/collaboration/internal/repository"
	"github.com/metlab/collaboration/internal/service"
	pb "metlab/proto-gen/go/collaboration"
	"github.com/metlab/shared/storage"
	"github.com/redis/go-redis/v9"
	"google.golang.org/grpc"
	"google.golang.org/grpc/health"
	"google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/reflection"
)

func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize database connection
	ctx := context.Background()
	database, err := db.New(ctx, cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer database.Close()

	log.Println("Successfully connected to database")

	// Initialize Redis client
	redisOpts, err := redis.ParseURL(cfg.RedisURL)
	if err != nil {
		log.Fatalf("Failed to parse Redis URL: %v", err)
	}
	
	redisClient := redis.NewClient(redisOpts)
	defer redisClient.Close()
	
	// Test Redis connection
	if err := redisClient.Ping(ctx).Err(); err != nil {
		log.Fatalf("Failed to connect to Redis: %v", err)
	}
	
	log.Println("Successfully connected to Redis")

	// Initialize S3 storage client
	storageConfig := &storage.Config{
		Endpoint:        fmt.Sprintf("http://%s", cfg.S3Endpoint),
		Region:          "us-east-1",
		AccessKeyID:     cfg.S3AccessKey,
		SecretAccessKey: cfg.S3SecretKey,
		UseSSL:          false,
		ForcePathStyle:  true,
	}
	
	storageClient, err := storage.NewClient(storageConfig)
	if err != nil {
		log.Fatalf("Failed to create storage client: %v", err)
	}
	
	// Ensure bucket exists
	bucketExists, err := storageClient.BucketExists(ctx, cfg.S3Bucket)
	if err != nil {
		log.Printf("Warning: Failed to check if bucket exists: %v", err)
	} else if !bucketExists {
		log.Printf("Creating bucket: %s", cfg.S3Bucket)
		if err := storageClient.CreateBucket(ctx, cfg.S3Bucket); err != nil {
			log.Printf("Warning: Failed to create bucket: %v", err)
		} else {
			log.Printf("Successfully created bucket: %s", cfg.S3Bucket)
		}
	}
	
	log.Println("Successfully initialized S3 storage client")

	// Initialize repositories
	studyGroupRepo := repository.NewStudyGroupRepository(database.Pool)
	chatRepo := repository.NewChatRepository(database.Pool)

	// Initialize service
	collaborationService := service.NewCollaborationService(
		cfg,
		studyGroupRepo,
		chatRepo,
		redisClient,
		storageClient,
	)

	// Initialize handler
	collaborationHandler := handler.NewCollaborationHandler(collaborationService)

	// Create gRPC server
	grpcServer := grpc.NewServer(
		grpc.UnaryInterceptor(loggingInterceptor),
	)

	// Register health check service
	healthServer := health.NewServer()
	grpc_health_v1.RegisterHealthServer(grpcServer, healthServer)
	
	// Set initial health status
	healthServer.SetServingStatus("", grpc_health_v1.HealthCheckResponse_SERVING)
	healthServer.SetServingStatus("collaboration.CollaborationService", grpc_health_v1.HealthCheckResponse_SERVING)

	// Register CollaborationService gRPC handler
	pb.RegisterCollaborationServiceServer(grpcServer, collaborationHandler)

	// Enable reflection for development
	reflection.Register(grpcServer)

	// Start listening
	lis, err := net.Listen("tcp", fmt.Sprintf(":%s", cfg.Port))
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}

	// Start server in a goroutine
	go func() {
		log.Printf("Collaboration service starting on port %s", cfg.Port)
		if err := grpcServer.Serve(lis); err != nil {
			log.Fatalf("Failed to serve: %v", err)
		}
	}()

	// Start background cleanup job
	go startCleanupJob(ctx, collaborationService, cfg)

	// Wait for interrupt signal to gracefully shutdown the server
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")

	// Set health status to not serving
	healthServer.SetServingStatus("", grpc_health_v1.HealthCheckResponse_NOT_SERVING)
	healthServer.SetServingStatus("collaboration.CollaborationService", grpc_health_v1.HealthCheckResponse_NOT_SERVING)

	// Graceful shutdown
	grpcServer.GracefulStop()
	log.Println("Server stopped")
}

// loggingInterceptor logs all gRPC requests
func loggingInterceptor(
	ctx context.Context,
	req interface{},
	info *grpc.UnaryServerInfo,
	handler grpc.UnaryHandler,
) (interface{}, error) {
	start := time.Now()
	
	// Call the handler
	resp, err := handler(ctx, req)
	
	// Log the request
	duration := time.Since(start)
	if err != nil {
		log.Printf("[ERROR] %s - %v (took %v)", info.FullMethod, err, duration)
	} else {
		log.Printf("[INFO] %s - success (took %v)", info.FullMethod, duration)
	}
	
	return resp, err
}

// startCleanupJob starts a background job to cleanup old messages
func startCleanupJob(ctx context.Context, svc *service.CollaborationService, cfg *config.Config) {
	ticker := time.NewTicker(24 * time.Hour) // Run once per day
	defer ticker.Stop()
	
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			log.Println("Running message cleanup job...")
			deleted, err := svc.CleanupOldMessages(ctx)
			if err != nil {
				log.Printf("Failed to cleanup old messages: %v", err)
			} else {
				log.Printf("Cleaned up %d old messages", deleted)
			}
		}
	}
}

