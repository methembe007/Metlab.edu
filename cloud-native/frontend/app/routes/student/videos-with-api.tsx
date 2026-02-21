import React, { useState, useEffect } from 'react';
import { VideoPlayer, VideoList, Video } from '../../components/video';
import { useVideoProgress } from '../../hooks/useVideoProgress';
import { fetchVideos } from '../../api/videoApi';

/**
 * Videos Page - Production version with API integration
 * 
 * This version fetches videos from the backend API and integrates
 * with the video progress tracking system.
 */
export default function VideosPage() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { trackProgress, handleVideoEnd, resetProgress } = useVideoProgress({
    videoId: selectedVideo?.id || '',
    onProgressUpdate: (data) => {
      console.log('Progress updated:', data);
      // Update local state
      setVideos((prevVideos) =>
        prevVideos.map((v) =>
          v.id === data.videoId
            ? { ...v, progress: data.currentTime }
            : v
        )
      );
    },
    updateInterval: 10000, // Update every 10 seconds
  });

  // Load videos from API on mount
  useEffect(() => {
    const loadVideos = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await fetchVideos();
        setVideos(response.videos);
        
        // Auto-select first video if none selected
        if (!selectedVideo && response.videos.length > 0) {
          setSelectedVideo(response.videos[0]);
        }
      } catch (err) {
        console.error('Error loading videos:', err);
        setError('Failed to load videos. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };

    loadVideos();
  }, []);

  const handleVideoSelect = (video: Video) => {
    setSelectedVideo(video);
    resetProgress();
  };

  const handleTimeUpdate = (currentTime: number) => {
    if (selectedVideo) {
      trackProgress(currentTime, selectedVideo.duration);
    }
  };

  const handleVideoEnded = () => {
    if (selectedVideo) {
      handleVideoEnd(selectedVideo.duration, selectedVideo.duration);
      
      // Auto-play next video
      const currentIndex = videos.findIndex((v) => v.id === selectedVideo.id);
      if (currentIndex < videos.length - 1) {
        setSelectedVideo(videos[currentIndex + 1]);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="loading-container" style={{ padding: '20px', textAlign: 'center' }}>
        <p>Loading videos...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container" style={{ padding: '20px', textAlign: 'center', color: 'red' }}>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  if (videos.length === 0) {
    return (
      <div className="empty-container" style={{ padding: '20px', textAlign: 'center' }}>
        <p>No videos available yet.</p>
      </div>
    );
  }

  return (
    <div className="videos-page" style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '20px' }}>Course Videos</h1>
      
      <div className="videos-layout" style={{ display: 'grid', gridTemplateColumns: '1fr 400px', gap: '20px' }}>
        <div className="video-player-section">
          {selectedVideo ? (
            <>
              <VideoPlayer
                videoUrl={selectedVideo.videoUrl}
                videoId={selectedVideo.id}
                currentTime={selectedVideo.progress || 0}
                onTimeUpdate={handleTimeUpdate}
                onEnded={handleVideoEnded}
              />
              <div className="video-details" style={{ marginTop: '20px' }}>
                <h2>{selectedVideo.title}</h2>
                <p style={{ color: '#666' }}>{selectedVideo.description}</p>
              </div>
            </>
          ) : (
            <div className="no-video-selected" style={{ padding: '40px', textAlign: 'center', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
              <p>Select a video from the list to start watching</p>
            </div>
          )}
        </div>

        <div className="video-list-section">
          <VideoList
            videos={videos}
            onVideoSelect={handleVideoSelect}
            currentVideoId={selectedVideo?.id}
          />
        </div>
      </div>
    </div>
  );
}
