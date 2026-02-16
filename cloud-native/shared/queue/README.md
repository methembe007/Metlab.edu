# Queue Package

A simple Redis-based job queue implementation for background job processing.

## Features

- Redis-backed job queue
- JSON serialization for job payloads
- Blocking dequeue with timeout
- Job retry tracking
- Queue size monitoring

## Usage

```go
package main

import (
    "context"
    "github.com/metlab/shared/queue"
    "github.com/redis/go-redis/v9"
)

func main() {
    // Create Redis client
    client := redis.NewClient(&redis.Options{
        Addr: "localhost:6379",
    })

    // Create queue
    q := queue.NewQueue(client, "video-processing")

    // Enqueue a job
    job := &queue.Job{
        ID:   "video-123",
        Type: "process_video",
        Payload: map[string]interface{}{
            "video_id": "video-123",
            "path":     "/tmp/video.mp4",
        },
    }
    
    err := q.Enqueue(context.Background(), job)
    if err != nil {
        panic(err)
    }

    // Dequeue a job (blocking with 5 second timeout)
    job, err = q.Dequeue(context.Background(), 5*time.Second)
    if err != nil {
        panic(err)
    }
    
    if job != nil {
        // Process the job
        processVideo(job)
    }
}
```

## Job Structure

```go
type Job struct {
    ID        string                 // Unique job identifier
    Type      string                 // Job type (e.g., "process_video")
    Payload   map[string]interface{} // Job-specific data
    CreatedAt time.Time              // Job creation timestamp
    Attempts  int                    // Number of processing attempts
}
```

## Queue Operations

- `Enqueue(ctx, job)` - Add a job to the queue
- `Dequeue(ctx, timeout)` - Retrieve and remove a job (blocking)
- `Size(ctx)` - Get the number of jobs in the queue
- `Clear(ctx)` - Remove all jobs from the queue

## Integration with Video Service

The video service uses this queue to process uploaded videos asynchronously:

1. Video is uploaded and stored
2. Processing job is enqueued
3. Worker picks up the job
4. Video is transcoded and thumbnails are generated
5. Video status is updated to "ready"
