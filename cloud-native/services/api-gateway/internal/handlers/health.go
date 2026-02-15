package handlers

import (
	"net/http"

	"github.com/metlab/api-gateway/internal/transformers"
)

// HealthResponse represents the health check response
type HealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

// Health handles health check requests
func (h *Handler) Health(w http.ResponseWriter, r *http.Request) {
	response := HealthResponse{
		Status:  "healthy",
		Message: "API Gateway is running",
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, response)
}

// Ready handles readiness check requests
func (h *Handler) Ready(w http.ResponseWriter, r *http.Request) {
	// TODO: Check if all gRPC connections are healthy
	response := HealthResponse{
		Status:  "ready",
		Message: "API Gateway is ready to accept requests",
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, response)
}
