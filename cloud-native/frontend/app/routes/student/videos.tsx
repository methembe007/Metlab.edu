import React, { useState, useEffect } from 'react';
import { VideoPlayer, VideoList, Video } from '../../components/video';
import { useVideoProgress } from '../../hooks/useVideoProgress';

// Mock data - in production, this would come from an API
const mockVideos: Video[] = [
  {
    id: 'video-1',
    title: 'Introduction to Cloud Computing',
    description: 'Learn the fundamentals of cloud computing and its benefits',
    thumbnailUrl: 'https://via.placeholder.com/160x90?text=Video+1',
    duration: 1200, // 20 minutes
    videoUrl: 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
    progress: 0,
  },
  {
    id: 'video-2',
    title: 'Kubernetes Basics',
    description: 'Understanding container orchestration with Kubernetes',
    thumbnailUrl: 'https://via.placeholder.com/160x90?text=Video+2',
    duration: 1800, // 30 minutes
    videoUrl: 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
    progress: 450, // 7.5 minutes watched
  },
  {
    id: 'video-3',
    title: 'Docker Containers',
    description: 'Deep dive into Docker and containerization',
    thumbnailUrl: 'https://via.placeholder.com/160x90?text=Video+3',
    duration: 2400, // 40 minutes
    videoUrl: 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
    progress: 2300, // Almost complete
  },
];

export default function VideosPage() {
  const [videos, setVideos] = useState<Video[]>(mockVideos);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [isLoading, setIsLoading] = useState(false);

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
      try {
        // In production, fetch from API
        // const response = await fetch('/api/videos');
        // const data = await response.json();
        // setVideos(data);
        
        // For now, use mock data
        setVideos(mockVideos);
        
        // Auto-select first video if none selected
        if (!selectedVideo && mockVideos.length > 0) {
          setSelectedVideo(mockVideos[0]);
        }
      } catch (error) {
        console.error('Error loading videos:', error);
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
