package queue

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

// Queue represents a Redis-based job queue
type Queue struct {
	client *redis.Client
	name   string
}

// Job represents a job in the queue
type Job struct {
	ID        string                 `json:"id"`
	Type      string                 `json:"type"`
	Payload   map[string]interface{} `json:"payload"`
	CreatedAt time.Time              `json:"created_at"`
	Attempts  int                    `json:"attempts"`
}

// NewQueue creates a new queue instance
func NewQueue(client *redis.Client, name string) *Queue {
	return &Queue{
		client: client,
		name:   name,
	}
}

// Enqueue adds a job to the queue
func (q *Queue) Enqueue(ctx context.Context, job *Job) error {
	if job.CreatedAt.IsZero() {
		job.CreatedAt = time.Now()
	}

	data, err := json.Marshal(job)
	if err != nil {
		return fmt.Errorf("failed to marshal job: %w", err)
	}

	return q.client.RPush(ctx, q.name, data).Err()
}

// Dequeue retrieves and removes a job from the queue
func (q *Queue) Dequeue(ctx context.Context, timeout time.Duration) (*Job, error) {
	result, err := q.client.BLPop(ctx, timeout, q.name).Result()
	if err != nil {
		if err == redis.Nil {
			return nil, nil // No job available
		}
		return nil, fmt.Errorf("failed to dequeue job: %w", err)
	}

	if len(result) < 2 {
		return nil, fmt.Errorf("invalid dequeue result")
	}

	var job Job
	if err := json.Unmarshal([]byte(result[1]), &job); err != nil {
		return nil, fmt.Errorf("failed to unmarshal job: %w", err)
	}

	return &job, nil
}

// Size returns the number of jobs in the queue
func (q *Queue) Size(ctx context.Context) (int64, error) {
	return q.client.LLen(ctx, q.name).Result()
}

// Clear removes all jobs from the queue
func (q *Queue) Clear(ctx context.Context) error {
	return q.client.Del(ctx, q.name).Err()
}
