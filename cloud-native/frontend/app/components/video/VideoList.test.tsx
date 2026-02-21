import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { VideoList, Video } from './VideoList';

describe('VideoList', () => {
  const mockVideos: Video[] = [
    {
      id: 'video-1',
      title: 'Test Video 1',
      description: 'Description 1',
      thumbnailUrl: 'https://example.com/thumb1.jpg',
      duration: 600,
      progress: 0,
      videoUrl: 'https://example.com/video1.m3u8',
    },
    {
      id: 'video-2',
      title: 'Test Video 2',
      description: 'Description 2',
      thumbnailUrl: 'https://example.com/thumb2.jpg',
      duration: 1200,
      progress: 600,
      videoUrl: 'https://example.com/video2.m3u8',
    },
    {
      id: 'video-3',
      title: 'Test Video 3',
      description: 'Description 3',
      thumbnailUrl: 'https://example.com/thumb3.jpg',
      duration: 1800,
      progress: 1710, // 95% complete
      videoUrl: 'https://example.com/video3.m3u8',
    },
  ];

  const mockOnVideoSelect = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders all videos', () => {
    render(<VideoList videos={mockVideos} onVideoSelect={mockOnVideoSelect} />);
    
    expect(screen.getByText('Test Video 1')).toBeInTheDocument();
    expect(screen.getByText('Test Video 2')).toBeInTheDocument();
    expect(screen.getByText('Test Video 3')).toBeInTheDocument();
  });

  it('renders video descriptions', () => {
    render(<VideoList videos={mockVideos} onVideoSelect={mockOnVideoSelect} />);
    
    expect(screen.getByText('Description 1')).toBeInTheDocument();
    expect(screen.getByText('Description 2')).toBeInTheDocument();
    expect(screen.getByText('Description 3')).toBeInTheDocument();
  });

  it('renders video thumbnails', () => {
    render(<VideoList videos={mockVideos} onVideoSelect={mockOnVideoSelect} />);
    
    const thumbnails = screen.getAllByRole('img');
    expect(thumbnails).toHaveLength(3);
    expect(thumbnails[0]).toHaveAttribute('src', 'https://example.com/thumb1.jpg');
  });

  it('displays duration for each video', () => {
    render(<VideoList videos={mockVideos} onVideoSelect={mockOnVideoSelect} />);
    
    expect(screen.getByText('10:00')).toBeInTheDocument(); // 600 seconds
    expect(screen.getByText('20:00')).toBeInTheDocument(); // 1200 seconds
    expect(screen.getByText('30:00')).toBeInTheDocument(); // 1800 seconds
  });

  it('shows progress percentage for videos in progress', () => {
    render(<VideoList videos={mockVideos} onVideoSelect={mockOnVideoSelect} />);
    
    expect(screen.getByText('50% watched')).toBeInTheDocument(); // video-2
  });

  it('shows completed status for videos >= 95% watched', () => {
    render(<VideoList videos={mockVideos} onVideoSelect={mockOnVideoSelect} />);
    
    expect(screen.getByText('✓ Completed')).toBeInTheDocument(); // video-3
  });

  it('calls onVideoSelect when video is clicked', () => {
    render(<VideoList videos={mockVideos} onVideoSelect={mockOnVideoSelect} />);
    
    const firstVideo = screen.getByText('Test Video 1').closest('.video-item');
    fireEvent.click(firstVideo!);
    
    expect(mockOnVideoSelect).toHaveBeenCalledWith(mockVideos[0]);
  });

  it('highlights currently selected video', () => {
    render(
      <VideoList
        videos={mockVideos}
        onVideoSelect={mockOnVideoSelect}
        currentVideoId="video-2"
      />
    );
    
    const secondVideo = screen.getByText('Test Video 2').closest('.video-item');
    expect(secondVideo).toHaveClass('active');
  });

  it('renders empty list when no videos provided', () => {
    render(<VideoList videos={[]} onVideoSelect={mockOnVideoSelect} />);
    
    expect(screen.getByText('Course Videos')).toBeInTheDocument();
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });

  it('calculates progress percentage correctly', () => {
    const { container } = render(
      <VideoList videos={mockVideos} onVideoSelect={mockOnVideoSelect} />
    );
    
    const progressBars = container.querySelectorAll('.progress-fill');
    expect(progressBars).toHaveLength(2); // Only videos with progress > 0
  });
});
