package handlers

import (
	"github.com/metlab/api-gateway/internal/grpc"
	authpb "github.com/metlab/shared/proto-gen/go/auth"
)

// Handler holds all HTTP handlers and their dependencies
type Handler struct {
	clients *grpc.ServiceClients
}

// NewHandler creates a new handler with gRPC clients
func NewHandler(clients *grpc.ServiceClients) *Handler {
	return &Handler{
		clients: clients,
	}
}

// GetAuthClient returns the auth service client for middleware use
func (h *Handler) GetAuthClient() authpb.AuthServiceClient {
	if h.clients == nil {
		return nil
	}
	return h.clients.Auth
}
