package middleware

import (
	"log"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5/middleware"
)

// RequestLogger is a custom logging middleware
func RequestLogger(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Create a wrapped response writer to capture status code
		ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)

		// Process request
		next.ServeHTTP(ww, r)

		// Log request details
		duration := time.Since(start)
		log.Printf(
			"[%s] %s %s - Status: %d - Duration: %v - Size: %d bytes",
			r.Method,
			r.URL.Path,
			r.RemoteAddr,
			ww.Status(),
			duration,
			ww.BytesWritten(),
		)
	})
}
