/**
 * Video API Client
 * Handles all video-related API calls to the backend
 */

export interface VideoProgressPayload {
  videoId: string;
  currentTime: number;
  duration: number;
  completed: boolean;
  timestamp: string;
}

export interface VideoData {
  id: string;
  title: string;
  description: string;
  thumbnailUrl: string;
  duration: number;
  progress?: number;
  videoUrl: string;
  courseId?: string;
  moduleId?: string;
}

export interface VideoListResponse {
  videos: VideoData[];
  totalCount: number;
}

/**
 * Fetch all videos for the current student
 */
export async function fetchVideos(courseId?: string): Promise<VideoListResponse> {
  const url = courseId ? `/api/videos?courseId=${courseId}` : '/api/videos';
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Include cookies for authentication
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch videos: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch a single video by ID
 */
export async function fetchVideoById(videoId: string): Promise<VideoData> {
  const response = await fetch(`/api/videos/${videoId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch video: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Update video progress
 */
export async function updateVideoProgress(
  payload: VideoProgressPayload
): Promise<void> {
  const response = await fetch('/api/video-progress', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to update video progress: ${response.statusText}`);
  }
}

/**
 * Get video progress for a specific video
 */
export async function getVideoProgress(videoId: string): Promise<number> {
  const response = await fetch(`/api/video-progress/${videoId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to get video progress: ${response.statusText}`);
  }

  const data = await response.json();
  return data.currentTime || 0;
}

/**
 * Mark video as completed
 */
export async function markVideoCompleted(videoId: string): Promise<void> {
  const response = await fetch(`/api/videos/${videoId}/complete`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to mark video as completed: ${response.statusText}`);
  }
}
