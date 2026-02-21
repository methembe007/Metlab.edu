import React, { useRef, useEffect, useState } from 'react';
import Hls from 'hls.js';

interface VideoPlayerProps {
  videoUrl: string;
  videoId: string;
  currentTime?: number;
  onTimeUpdate?: (time: number) => void;
  onEnded?: () => void;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  videoUrl,
  videoId,
  currentTime = 0,
  onTimeUpdate,
  onEnded,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [progress, setProgress] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (Hls.isSupported() && videoUrl.includes('.m3u8')) {
      const hls = new Hls();
      hlsRef.current = hls;
      hls.loadSource(videoUrl);
      hls.attachMedia(video);
      
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        if (currentTime > 0) {
          video.currentTime = currentTime;
        }
      });

      hls.on(Hls.Events.ERROR, (event, data) => {
        console.error('HLS error:', data);
      });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = videoUrl;
      video.addEventListener('loadedmetadata', () => {
        if (currentTime > 0) {
          video.currentTime = currentTime;
        }
      });
    } else {
      video.src = videoUrl;
      if (currentTime > 0) {
        video.currentTime = currentTime;
      }
    }

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
      }
    };
  }, [videoUrl, videoId]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setProgress(video.currentTime);
      if (onTimeUpdate) {
        onTimeUpdate(video.currentTime);
      }
    };

    const handleLoadedMetadata = () => {
      setDuration(video.duration);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      if (onEnded) {
        onEnded();
      }
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('ended', handleEnded);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('ended', handleEnded);
    };
  }, [onTimeUpdate, onEnded]);

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (time: number) => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = time;
    setProgress(time);
  };

  const handlePlaybackRateChange = (rate: number) => {
    const video = videoRef.current;
    if (!video) return;
    video.playbackRate = rate;
    setPlaybackRate(rate);
  };

  const handleVolumeChange = (newVolume: number) => {
    const video = videoRef.current;
    if (!video) return;
    video.volume = newVolume;
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };

  const toggleMute = () => {
    const video = videoRef.current;
    if (!video) return;
    video.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const formatTime = (seconds: number): string => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="video-player-container">
      <video
        ref={videoRef}
        className="video-element"
        style={{ width: '100%', maxHeight: '70vh' }}
      />
      
      <div className="video-controls">
        <div className="progress-bar-container">
          <input
            type="range"
            min="0"
            max={duration || 0}
            value={progress}
            onChange={(e) => handleSeek(Number(e.target.value))}
            className="progress-bar"
            style={{ width: '100%' }}
          />
          <div className="time-display">
            <span>{formatTime(progress)}</span>
            <span> / </span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        <div className="control-buttons">
          <button onClick={togglePlay} className="control-btn">
            {isPlaying ? '⏸ Pause' : '▶ Play'}
          </button>

          <div className="playback-speed">
            <label>Speed: </label>
            <select
              value={playbackRate}
              onChange={(e) => handlePlaybackRateChange(Number(e.target.value))}
              className="speed-select"
            >
              <option value="0.5">0.5x</option>
              <option value="0.75">0.75x</option>
              <option value="1">1x</option>
              <option value="1.25">1.25x</option>
              <option value="1.5">1.5x</option>
              <option value="2">2x</option>
            </select>
          </div>

          <div className="volume-control">
            <button onClick={toggleMute} className="control-btn">
              {isMuted ? '🔇' : '🔊'}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={isMuted ? 0 : volume}
              onChange={(e) => handleVolumeChange(Number(e.target.value))}
              className="volume-slider"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
