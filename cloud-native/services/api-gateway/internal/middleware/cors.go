package middleware

import (
	"net/http"
	"os"
	"strings"

	"github.com/go-chi/cors"
)

// GetCORSHandler returns a configured CORS handler
func GetCORSHandler() func(next http.Handler) http.Handler {
	allowedOrigins := getAllowedOrigins()

	return cors.Handler(cors.Options{
		AllowedOrigins: allowedOrigins,
		AllowedMethods: []string{
			"GET",
			"POST",
			"PUT",
			"PATCH",
			"DELETE",
			"OPTIONS",
		},
		AllowedHeaders: []string{
			"Accept",
			"Authorization",
			"Content-Type",
			"X-CSRF-Token",
			"X-Request-ID",
		},
		ExposedHeaders: []string{
			"Link",
			"X-Total-Count",
			"X-Request-ID",
		},
		AllowCredentials: true,
		MaxAge:           300, // 5 minutes
	})
}

// getAllowedOrigins returns the list of allowed origins from environment or defaults
func getAllowedOrigins() []string {
	originsEnv := os.Getenv("ALLOWED_ORIGINS")
	if originsEnv == "" {
		// Default origins for development
		return []string{
			"http://localhost:3000",
			"http://localhost:5173",
			"http://127.0.0.1:3000",
			"http://127.0.0.1:5173",
		}
	}

	// Split comma-separated origins
	origins := strings.Split(originsEnv, ",")
	for i, origin := range origins {
		origins[i] = strings.TrimSpace(origin)
	}

	return origins
}
