import React from 'react';

export interface Video {
  id: string;
  title: string;
  description: string;
  thumbnailUrl: string;
  duration: number;
  progress?: number;
  videoUrl: string;
}

interface VideoListProps {
  videos: Video[];
  onVideoSelect: (video: Video) => void;
  currentVideoId?: string;
}

export const VideoList: React.FC<VideoListProps> = ({
  videos,
  onVideoSelect,
  currentVideoId,
}) => {
  const formatDuration = (seconds: number): string => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const calculateProgressPercentage = (video: Video): number => {
    if (!video.progress || video.duration === 0) return 0;
    return (video.progress / video.duration) * 100;
  };

  return (
    <div className="video-list">
      <h2 className="video-list-title">Course Videos</h2>
      <div className="video-items">
        {videos.map((video) => {
          const progressPercentage = calculateProgressPercentage(video);
          const isActive = currentVideoId === video.id;

          return (
            <div
              key={video.id}
              className={`video-item ${isActive ? 'active' : ''}`}
              onClick={() => onVideoSelect(video)}
              style={{
                cursor: 'pointer',
                padding: '12px',
                marginBottom: '12px',
                border: isActive ? '2px solid #007bff' : '1px solid #ddd',
                borderRadius: '8px',
                backgroundColor: isActive ? '#f0f8ff' : '#fff',
              }}
            >
              <div className="video-item-content" style={{ display: 'flex', gap: '12px' }}>
                <div className="thumbnail-container" style={{ position: 'relative', flexShrink: 0 }}>
                  <img
                    src={video.thumbnailUrl}
                    alt={video.title}
                    className="video-thumbnail"
                    style={{
                      width: '160px',
                      height: '90px',
                      objectFit: 'cover',
                      borderRadius: '4px',
                    }}
                  />
                  <div
                    className="duration-badge"
                    style={{
                      position: 'absolute',
                      bottom: '4px',
                      right: '4px',
                      backgroundColor: 'rgba(0, 0, 0, 0.8)',
                      color: '#fff',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      fontSize: '12px',
                    }}
                  >
                    {formatDuration(video.duration)}
                  </div>
                  {progressPercentage > 0 && (
                    <div
                      className="progress-overlay"
                      style={{
                        position: 'absolute',
                        bottom: 0,
                        left: 0,
                        right: 0,
                        height: '4px',
                        backgroundColor: 'rgba(0, 0, 0, 0.3)',
                        borderRadius: '0 0 4px 4px',
                      }}
                    >
                      <div
                        className="progress-fill"
                        style={{
                          height: '100%',
                          width: `${progressPercentage}%`,
                          backgroundColor: '#007bff',
                          borderRadius: '0 0 4px 4px',
                        }}
                      />
                    </div>
                  )}
                </div>

                <div className="video-info" style={{ flex: 1 }}>
                  <h3 className="video-title" style={{ margin: '0 0 8px 0', fontSize: '16px' }}>
                    {video.title}
                  </h3>
                  <p className="video-description" style={{ margin: 0, fontSize: '14px', color: '#666' }}>
                    {video.description}
                  </p>
                  {progressPercentage > 0 && (
                    <div className="progress-text" style={{ marginTop: '8px', fontSize: '12px', color: '#007bff' }}>
                      {progressPercentage >= 95
                        ? '✓ Completed'
                        : `${Math.round(progressPercentage)}% watched`}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
