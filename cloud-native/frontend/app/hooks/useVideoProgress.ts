import { useEffect, useRef, useCallback } from 'react';

interface VideoProgressData {
  videoId: string;
  currentTime: number;
  duration: number;
  completed: boolean;
}

interface UseVideoProgressOptions {
  videoId: string;
  onProgressUpdate?: (data: VideoProgressData) => void;
  updateInterval?: number; // milliseconds
  apiEndpoint?: string;
}

export const useVideoProgress = ({
  videoId,
  onProgressUpdate,
  updateInterval = 10000, // Default: update every 10 seconds
  apiEndpoint = '/api/video-progress',
}: UseVideoProgressOptions) => {
  const lastUpdateTime = useRef<number>(0);
  const accumulatedTime = useRef<number>(0);
  const lastCurrentTime = useRef<number>(0);

  const sendProgressToBackend = useCallback(
    async (data: VideoProgressData) => {
      try {
        const response = await fetch(apiEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            videoId: data.videoId,
            currentTime: data.currentTime,
            duration: data.duration,
            completed: data.completed,
            timestamp: new Date().toISOString(),
          }),
        });

        if (!response.ok) {
          console.error('Failed to update video progress:', response.statusText);
        }
      } catch (error) {
        console.error('Error sending video progress:', error);
      }
    },
    [apiEndpoint]
  );

  const trackProgress = useCallback(
    (currentTime: number, duration: number) => {
      const now = Date.now();
      
      // Calculate viewing time (only if video is actually playing forward)
      if (lastCurrentTime.current > 0 && currentTime > lastCurrentTime.current) {
        const timeDiff = currentTime - lastCurrentTime.current;
        // Only count if the difference is reasonable (not seeking)
        if (timeDiff > 0 && timeDiff < 5) {
          accumulatedTime.current += timeDiff;
        }
      }
      
      lastCurrentTime.current = currentTime;

      // Check if it's time to send an update
      if (now - lastUpdateTime.current >= updateInterval) {
        const completed = currentTime / duration >= 0.95; // 95% completion threshold
        
        const progressData: VideoProgressData = {
          videoId,
          currentTime,
          duration,
          completed,
        };

        // Send to backend
        sendProgressToBackend(progressData);

        // Call optional callback
        if (onProgressUpdate) {
          onProgressUpdate(progressData);
        }

        lastUpdateTime.current = now;
      }
    },
    [videoId, updateInterval, onProgressUpdate, sendProgressToBackend]
  );

  const handleVideoEnd = useCallback(
    (currentTime: number, duration: number) => {
      const progressData: VideoProgressData = {
        videoId,
        currentTime,
        duration,
        completed: true,
      };

      // Send final update
      sendProgressToBackend(progressData);

      if (onProgressUpdate) {
        onProgressUpdate(progressData);
      }
    },
    [videoId, onProgressUpdate, sendProgressToBackend]
  );

  const resetProgress = useCallback(() => {
    lastUpdateTime.current = 0;
    accumulatedTime.current = 0;
    lastCurrentTime.current = 0;
  }, []);

  // Cleanup on unmount - send final progress
  useEffect(() => {
    return () => {
      if (lastCurrentTime.current > 0) {
        sendProgressToBackend({
          videoId,
          currentTime: lastCurrentTime.current,
          duration: 0,
          completed: false,
        });
      }
    };
  }, [videoId, sendProgressToBackend]);

  return {
    trackProgress,
    handleVideoEnd,
    resetProgress,
    accumulatedTime: accumulatedTime.current,
  };
};
