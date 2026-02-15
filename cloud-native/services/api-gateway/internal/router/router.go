package router

import (
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"

	"github.com/metlab/api-gateway/internal/handlers"
	custommw "github.com/metlab/api-gateway/internal/middleware"
	"github.com/metlab/shared/cache"
)

// RouterConfig holds configuration for the router
type RouterConfig struct {
	RedisClient        *cache.RedisClient
	RateLimitPerMinute int
}

// NewRouter creates and configures the main router
func NewRouter(handler *handlers.Handler, config *RouterConfig) *chi.Mux {
	r := chi.NewRouter()

	// Global middleware
	r.Use(middleware.RequestID)
	r.Use(custommw.RequestID)
	r.Use(custommw.RequestLogger)
	r.Use(middleware.Recoverer)
	r.Use(custommw.GetCORSHandler())

	// Apply rate limiting middleware
	if config != nil {
		rateLimitConfig := &custommw.RateLimitConfig{
			Limit:  config.RateLimitPerMinute,
			Window: time.Minute,
			KeyFunc: func(r *http.Request) string {
				// Use X-Forwarded-For if behind proxy, otherwise RemoteAddr
				if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
					return xff
				}
				if xri := r.Header.Get("X-Real-IP"); xri != "" {
					return xri
				}
				return r.RemoteAddr
			},
		}
		
		if config.RedisClient != nil {
			rateLimitConfig.RedisClient = config.RedisClient.Client()
		}
		
		r.Use(custommw.RateLimit(rateLimitConfig))
	}

	// Health check endpoints (no auth required)
	r.Get("/health", handler.Health)
	r.Get("/ready", handler.Ready)

	// API routes
	r.Route("/api", func(r chi.Router) {
		// Root API endpoint
		r.Get("/", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.Write([]byte(`{"message":"Metlab API Gateway","version":"1.0.0"}`))
		})

		// Auth endpoints (no auth middleware)
		r.Route("/auth", func(r chi.Router) {
			r.Post("/teacher/signup", handler.TeacherSignup)
			r.Post("/teacher/login", handler.TeacherLogin)
			r.Post("/student/signin", handler.StudentSignin)
			r.Post("/codes/generate", handler.GenerateSigninCode)
		})

		// Protected endpoints (require authentication)
		r.Group(func(r chi.Router) {
			// Add authentication middleware
			if handler.GetAuthClient() != nil {
				r.Use(custommw.Authenticate(handler.GetAuthClient()))
			}

			// Video endpoints
			r.Route("/videos", func(r chi.Router) {
				r.Get("/", handler.ListVideos)
				r.Post("/", handler.UploadVideo)
				r.Get("/{id}", handler.GetVideo)
				r.Get("/{id}/stream", handler.GetStreamingURL)
				r.Post("/{id}/view", handler.RecordView)
				r.Get("/{id}/analytics", handler.GetVideoAnalytics)
			})

			// Homework endpoints
			r.Route("/homework", func(r chi.Router) {
				r.Route("/assignments", func(r chi.Router) {
					r.Post("/", handler.CreateAssignment)
					r.Get("/", handler.ListAssignments)
				})
				r.Route("/submissions", func(r chi.Router) {
					r.Post("/", handler.SubmitHomework)
					r.Get("/", handler.ListSubmissions)
					r.Post("/{id}/grade", handler.GradeSubmission)
					r.Get("/{id}/file", handler.GetSubmissionFile)
				})
			})

			// PDF endpoints
			r.Route("/pdfs", func(r chi.Router) {
				r.Post("/", handler.UploadPDF)
				r.Get("/", handler.ListPDFs)
				r.Get("/{id}/download", handler.GetPDFDownloadURL)
			})

			// Analytics endpoints
			r.Route("/analytics", func(r chi.Router) {
				r.Get("/login-stats", handler.GetLoginStats)
				r.Get("/class-engagement", handler.GetClassEngagement)
				r.Post("/login", handler.RecordLogin)
			})

			// Study group endpoints
			r.Route("/study-groups", func(r chi.Router) {
				r.Post("/", handler.CreateStudyGroup)
				r.Get("/", handler.ListStudyGroups)
				r.Post("/{id}/join", handler.JoinStudyGroup)
			})

			// Chat endpoints
			r.Route("/chat", func(r chi.Router) {
				r.Route("/rooms", func(r chi.Router) {
					r.Post("/", handler.CreateChatRoom)
					r.Post("/{id}/messages", handler.SendMessage)
					r.Get("/{id}/messages", handler.GetMessages)
				})
			})
		})
	})

	return r
}
