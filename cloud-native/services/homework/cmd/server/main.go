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

	"github.com/metlab/homework/internal/config"
	"github.com/metlab/homework/internal/handler"
	"github.com/metlab/shared/db"
	"github.com/metlab/shared/logger"
	pb "github.com/metlab/shared/proto-gen/go/homework"
	"github.com/metlab/shared/storage"
	"google.golang.org/grpc"
	"google.golang.org/grpc/health"
	"google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/reflection"
)

func main() {
	// Load configuration
	cfg, err := config.LoadConfig()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Initialize logger
	logLevel := logger.InfoLevel
	if cfg.Environment == "development" {
		logLevel = logger.DebugLevel
	}
	
	appLogger := logger.New(&logger.Config{
		Level:       logLevel,
		ServiceName: "homework-service",
	})

	appLogger.Info("Starting Homework Service", map[string]interface{}{
		"port":        cfg.Port,
		"environment": cfg.Environment,
	})

	// Initialize database connection
	ctx := context.Background()
	dbPool, err := db.NewPoolFromURL(ctx, cfg.DatabaseURL)
	if err != nil {
		appLogger.Fatal("Failed to connect to database", err)
	}
	defer dbPool.Close()

	appLogger.Info("Database connection established")

	// Initialize S3 storage client
	storageClient, err := storage.NewS3Client(&storage.S3Config{
		Endpoint:  cfg.S3Endpoint,
		AccessKey: cfg.S3AccessKey,
		SecretKey: cfg.S3SecretKey,
		Bucket:    cfg.S3Bucket,
		Region:    cfg.S3Region,
		UseSSL:    cfg.S3UseSSL,
	})
	if err != nil {
		appLogger.Fatal("Failed to initialize storage client", err)
	}

	appLogger.Info("Storage client initialized", map[string]interface{}{
		"bucket": cfg.S3Bucket,
	})

	// Create gRPC server
	grpcServer := grpc.NewServer(
		grpc.MaxRecvMsgSize(int(cfg.MaxUploadSize)),
		grpc.MaxSendMsgSize(int(cfg.MaxUploadSize)),
	)

	// Register homework service
	homeworkHandler := handler.NewHomeworkHandler(
		dbPool,
		storageClient,
		appLogger,
		cfg.MaxUploadSize,
	)
	pb.RegisterHomeworkServiceServer(grpcServer, homeworkHandler)

	// Register health check service
	healthServer := health.NewServer()
	grpc_health_v1.RegisterHealthServer(grpcServer, healthServer)
	healthServer.SetServingStatus("", grpc_health_v1.HealthCheckResponse_SERVING)

	// Register reflection service for development
	if cfg.Environment == "development" {
		reflection.Register(grpcServer)
		appLogger.Info("gRPC reflection enabled")
	}

	// Start listening
	lis, err := net.Listen("tcp", fmt.Sprintf(":%s", cfg.Port))
	if err != nil {
		appLogger.Fatal("Failed to listen", err)
	}

	// Handle graceful shutdown
	go func() {
		sigChan := make(chan os.Signal, 1)
		signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
		<-sigChan

		appLogger.Info("Shutting down gracefully...")
		
		// Set health check to not serving
		healthServer.SetServingStatus("", grpc_health_v1.HealthCheckResponse_NOT_SERVING)
		
		// Give ongoing requests time to complete
		time.Sleep(5 * time.Second)
		
		grpcServer.GracefulStop()
		appLogger.Info("Server stopped")
		os.Exit(0)
	}()

	appLogger.Info("Homework service listening", map[string]interface{}{
		"address": lis.Addr().String(),
	})
	
	if err := grpcServer.Serve(lis); err != nil {
		appLogger.Fatal("Failed to serve", err)
	}
}
