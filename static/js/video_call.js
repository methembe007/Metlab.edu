/**
 * Video Call Interface - WebRTC Connection Management
 * Handles peer-to-peer video/audio connections and signaling
 */

class VideoCallInterface {
    constructor(sessionId, userId, userName) {
        this.sessionId = sessionId;
        this.userId = userId;
        this.userName = userName;
        
        // WebSocket connection
        this.ws = null;
        this.wsReconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        // WebRTC connections - map of userId to RTCPeerConnection
        this.peerConnections = new Map();
        
        // Media streams
        this.localStream = null;
        this.remoteStreams = new Map(); // userId -> MediaStream
        
        // Media state
        this.audioEnabled = true;
        this.videoEnabled = true;
        this.screenSharing = false;
        this.screenStream = null;
        
        // Connection quality monitoring
        this.connectionStats = new Map(); // userId -> stats
        this.statsInterval = null;
        
        // ICE servers configuration
        this.iceServers = [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
            { urls: 'stun:stun2.l.google.com:19302' }
        ];
        
        // Participants data
        this.participants = new Map(); // userId -> participant data
        
        // UI elements (will be set after DOM loads)
        this.elements = {};
        
        // Bind methods
        this.handleWebSocketMessage = this.handleWebSocketMessage.bind(this);
        this.handleWebSocketClose = this.handleWebSocketClose.bind(this);
        this.handleWebSocketError = this.handleWebSocketError.bind(this);
    }
    
    /**
     * Initialize the video call interface
     */
    async initialize() {
        try {
            // Initialize local video placeholder with user initials
            this.initializeLocalPlaceholder();
            
            // Get local media stream
            await this.getLocalStream();
            
            // Connect to WebSocket signaling server
            this.connectWebSocket();
            
            // Set up UI event listeners
            this.setupUIListeners();
            
            // Start connection quality monitoring
            this.startConnectionMonitoring();
            
            console.log('Video call interface initialized');
        } catch (error) {
            console.error('Failed to initialize video call:', error);
            this.showError('Failed to initialize video call: ' + error.message);
        }
    }
    
    /**
     * Connect to WebSocket signaling server
     */
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/video/${this.sessionId}/`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.wsReconnectAttempts = 0;
            
            // Join the session
            this.sendWebSocketMessage({
                type: 'join_session',
                user_id: this.userId,
                user_name: this.userName,
                audio_enabled: this.audioEnabled,
                video_enabled: this.videoEnabled
            });
        };
        
        this.ws.onmessage = this.handleWebSocketMessage;
        this.ws.onclose = this.handleWebSocketClose;
        this.ws.onerror = this.handleWebSocketError;
    }

    
    /**
     * Handle incoming WebSocket messages
     */
    async handleWebSocketMessage(event) {
        try {
            const message = JSON.parse(event.data);
            console.log('WebSocket message received:', message.type);
            
            switch (message.type) {
                case 'participant_joined':
                    await this.handleParticipantJoined(message);
                    break;
                    
                case 'participant_left':
                    this.handleParticipantLeft(message);
                    break;
                    
                case 'webrtc_offer':
                    await this.handleOffer(message);
                    break;
                    
                case 'webrtc_answer':
                    await this.handleAnswer(message);
                    break;
                    
                case 'ice_candidate':
                    await this.handleICECandidate(message);
                    break;
                    
                case 'media_state_change':
                    this.handleMediaStateChange(message);
                    break;
                    
                case 'screen_share_start':
                    this.handleScreenShareStart(message);
                    break;
                    
                case 'screen_share_stop':
                    this.handleScreenShareStop(message);
                    break;
                    
                case 'participants_list':
                    this.handleParticipantsList(message);
                    break;
                    
                case 'error':
                    this.showError(message.message);
                    break;
                    
                default:
                    console.warn('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Error handling WebSocket message:', error);
        }
    }
    
    /**
     * Handle WebSocket close event
     */
    handleWebSocketClose(event) {
        console.log('WebSocket closed:', event.code, event.reason);
        
        // Attempt to reconnect
        if (this.wsReconnectAttempts < this.maxReconnectAttempts) {
            this.wsReconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.wsReconnectAttempts), 30000);
            
            console.log(`Reconnecting in ${delay}ms (attempt ${this.wsReconnectAttempts})`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, delay);
        } else {
            this.showError('Connection lost. Please refresh the page.');
        }
    }
    
    /**
     * Handle WebSocket error event
     */
    handleWebSocketError(error) {
        console.error('WebSocket error:', error);
    }
    
    /**
     * Send message through WebSocket
     */
    sendWebSocketMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.error('WebSocket not connected');
        }
    }

    
    /**
     * Create RTCPeerConnection for a peer
     */
    createPeerConnection(peerId) {
        console.log('Creating peer connection for:', peerId);
        
        const pc = new RTCPeerConnection({
            iceServers: this.iceServers
        });
        
        // Add local stream tracks
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => {
                pc.addTrack(track, this.localStream);
            });
        }
        
        // Handle ICE candidates
        pc.onicecandidate = (event) => {
            if (event.candidate) {
                this.sendWebSocketMessage({
                    type: 'ice_candidate',
                    target_user_id: peerId,
                    candidate: event.candidate.toJSON()
                });
            }
        };
        
        // Handle connection state changes
        pc.onconnectionstatechange = () => {
            console.log(`Connection state for ${peerId}:`, pc.connectionState);
            
            if (pc.connectionState === 'failed') {
                // Attempt ICE restart
                this.restartICE(peerId);
            } else if (pc.connectionState === 'disconnected') {
                // Monitor for reconnection
                setTimeout(() => {
                    if (pc.connectionState === 'disconnected') {
                        this.restartICE(peerId);
                    }
                }, 5000);
            }
            
            // Update connection state display
            this.updateConnectionStateDisplay(pc.connectionState);
            this.updateConnectionQuality(peerId, pc.connectionState);
        };
        
        // Handle ICE connection state changes
        pc.oniceconnectionstatechange = () => {
            console.log(`ICE connection state for ${peerId}:`, pc.iceConnectionState);
        };
        
        // Handle remote stream
        pc.ontrack = (event) => {
            console.log('Received remote track from:', peerId);
            
            if (!this.remoteStreams.has(peerId)) {
                this.remoteStreams.set(peerId, new MediaStream());
            }
            
            const stream = this.remoteStreams.get(peerId);
            stream.addTrack(event.track);
            
            // Display remote video
            this.displayRemoteVideo(peerId, stream);
        };
        
        this.peerConnections.set(peerId, pc);
        return pc;
    }

    
    /**
     * Handle participant joined event
     */
    async handleParticipantJoined(message) {
        const peerId = message.user_id;
        
        if (peerId === this.userId) {
            // This is us, ignore
            return;
        }
        
        console.log('Participant joined:', message.user_name);
        
        // Add to participants list
        this.participants.set(peerId, {
            userId: peerId,
            userName: message.user_name,
            audioEnabled: message.audio_enabled,
            videoEnabled: message.video_enabled,
            joinedAt: new Date()
        });
        
        // Update UI
        this.updateParticipantsList();
        
        // Create peer connection and send offer
        const pc = this.createPeerConnection(peerId);
        
        try {
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            
            this.sendWebSocketMessage({
                type: 'webrtc_offer',
                target_user_id: peerId,
                offer: {
                    type: offer.type,
                    sdp: offer.sdp
                }
            });
        } catch (error) {
            console.error('Error creating offer:', error);
        }
    }
    
    /**
     * Handle WebRTC offer
     */
    async handleOffer(message) {
        const peerId = message.from_user_id;
        console.log('Received offer from:', peerId);
        
        let pc = this.peerConnections.get(peerId);
        if (!pc) {
            pc = this.createPeerConnection(peerId);
        }
        
        try {
            await pc.setRemoteDescription(new RTCSessionDescription(message.offer));
            
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            
            this.sendWebSocketMessage({
                type: 'webrtc_answer',
                target_user_id: peerId,
                answer: {
                    type: answer.type,
                    sdp: answer.sdp
                }
            });
        } catch (error) {
            console.error('Error handling offer:', error);
        }
    }
    
    /**
     * Handle WebRTC answer
     */
    async handleAnswer(message) {
        const peerId = message.from_user_id;
        console.log('Received answer from:', peerId);
        
        const pc = this.peerConnections.get(peerId);
        if (pc) {
            try {
                await pc.setRemoteDescription(new RTCSessionDescription(message.answer));
            } catch (error) {
                console.error('Error handling answer:', error);
            }
        }
    }
    
    /**
     * Handle ICE candidate
     */
    async handleICECandidate(message) {
        const peerId = message.from_user_id;
        const pc = this.peerConnections.get(peerId);
        
        if (pc) {
            try {
                await pc.addIceCandidate(new RTCIceCandidate(message.candidate));
            } catch (error) {
                console.error('Error adding ICE candidate:', error);
            }
        }
    }
    
    /**
     * Handle participant left event
     */
    handleParticipantLeft(message) {
        const peerId = message.user_id;
        console.log('Participant left:', peerId);
        
        // Close peer connection
        const pc = this.peerConnections.get(peerId);
        if (pc) {
            pc.close();
            this.peerConnections.delete(peerId);
        }
        
        // Remove remote stream
        this.remoteStreams.delete(peerId);
        
        // Remove from participants
        this.participants.delete(peerId);
        
        // Update UI
        this.removeRemoteVideo(peerId);
        this.updateParticipantsList();
    }
    
    /**
     * Handle participants list (initial state)
     */
    handleParticipantsList(message) {
        console.log('Received participants list:', message.participants);
        
        message.participants.forEach(participant => {
            if (participant.user_id !== this.userId) {
                this.participants.set(participant.user_id, {
                    userId: participant.user_id,
                    userName: participant.user_name,
                    audioEnabled: participant.audio_enabled,
                    videoEnabled: participant.video_enabled,
                    joinedAt: new Date(participant.joined_at)
                });
            }
        });
        
        this.updateParticipantsList();
    }

    
    /**
     * Restart ICE connection
     */
    async restartICE(peerId) {
        console.log('Restarting ICE for:', peerId);
        
        const pc = this.peerConnections.get(peerId);
        if (pc) {
            try {
                const offer = await pc.createOffer({ iceRestart: true });
                await pc.setLocalDescription(offer);
                
                this.sendWebSocketMessage({
                    type: 'webrtc_offer',
                    target_user_id: peerId,
                    offer: {
                        type: offer.type,
                        sdp: offer.sdp
                    }
                });
            } catch (error) {
                console.error('Error restarting ICE:', error);
            }
        }
    }
    
    /**
     * Start monitoring connection quality
     */
    startConnectionMonitoring() {
        this.statsInterval = setInterval(() => {
            this.peerConnections.forEach((pc, peerId) => {
                this.getConnectionStats(peerId, pc);
            });
        }, 2000);
    }
    
    /**
     * Get connection statistics
     */
    async getConnectionStats(peerId, pc) {
        try {
            const stats = await pc.getStats();
            let quality = 'unknown';
            let bytesReceived = 0;
            let packetsLost = 0;
            
            stats.forEach(report => {
                if (report.type === 'inbound-rtp' && report.kind === 'video') {
                    bytesReceived = report.bytesReceived || 0;
                    packetsLost = report.packetsLost || 0;
                }
            });
            
            // Simple quality calculation based on packet loss
            const totalPackets = packetsLost + (bytesReceived / 1000);
            const lossRate = totalPackets > 0 ? packetsLost / totalPackets : 0;
            
            if (lossRate < 0.02) {
                quality = 'excellent';
            } else if (lossRate < 0.05) {
                quality = 'good';
            } else if (lossRate < 0.10) {
                quality = 'fair';
            } else {
                quality = 'poor';
            }
            
            this.connectionStats.set(peerId, { quality, lossRate, bytesReceived });
            this.updateConnectionQuality(peerId, quality);
        } catch (error) {
            console.error('Error getting connection stats:', error);
        }
    }
    
    /**
     * Update connection quality indicator
     */
    updateConnectionQuality(peerId, quality) {
        const qualityElement = document.querySelector(`[data-peer-id="${peerId}"] .connection-quality`);
        if (qualityElement) {
            qualityElement.className = `connection-quality quality-${quality}`;
            qualityElement.title = `Connection: ${quality}`;
        }
        
        // Update overall connection quality in control bar
        this.updateOverallConnectionQuality();
    }
    
    /**
     * Show error message
     */
    showError(message) {
        console.error('Error:', message);
        
        // Display error in UI
        const errorContainer = document.getElementById('error-container');
        if (errorContainer) {
            errorContainer.textContent = message;
            errorContainer.style.display = 'block';
            
            setTimeout(() => {
                errorContainer.style.display = 'none';
            }, 5000);
        } else {
            alert(message);
        }
    }
    
    /**
     * Clean up resources
     */
    cleanup() {
        console.log('Cleaning up video call interface');
        
        // Stop monitoring
        if (this.statsInterval) {
            clearInterval(this.statsInterval);
        }
        
        // Close all peer connections
        this.peerConnections.forEach(pc => pc.close());
        this.peerConnections.clear();
        
        // Stop local stream
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
        }
        
        // Stop screen stream
        if (this.screenStream) {
            this.screenStream.getTracks().forEach(track => track.stop());
        }
        
        // Close WebSocket
        if (this.ws) {
            this.ws.close();
        }
    }
}


// ============================================================================
// Media Stream Handling - Task 4.2 Implementation
// ============================================================================

/**
 * Initialize local video placeholder
 */
VideoCallInterface.prototype.initializeLocalPlaceholder = function() {
    const placeholder = document.getElementById('local-video-placeholder');
    if (placeholder) {
        const avatar = placeholder.querySelector('.avatar');
        if (avatar && !avatar.textContent.trim()) {
            avatar.textContent = this.getInitials(this.userName);
        }
    }
};

/**
 * Get local media stream (audio and video)
 * Implements: Capture local audio/video streams with fallback options
 */
VideoCallInterface.prototype.getLocalStream = async function() {
    try {
        const constraints = {
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            },
            video: {
                width: { ideal: 1280, max: 1920 },
                height: { ideal: 720, max: 1080 },
                frameRate: { ideal: 30, max: 60 },
                facingMode: 'user'
            }
        };
        
        this.localStream = await navigator.mediaDevices.getUserMedia(constraints);
        console.log('Local stream acquired with video and audio');
        
        // Display local video
        this.displayLocalVideo();
        
        return this.localStream;
    } catch (error) {
        console.error('Error getting local stream:', error);
        
        if (error.name === 'NotAllowedError') {
            throw new Error('Camera/microphone access denied. Please grant permissions and reload the page.');
        } else if (error.name === 'NotFoundError') {
            // Try audio-only fallback
            try {
                console.log('Camera not found, trying audio-only mode');
                this.localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                this.videoEnabled = false;
                
                // Show placeholder for local video
                this.showLocalVideoPlaceholder(true);
                this.updateVideoButton();
                
                console.log('Audio-only stream acquired');
                return this.localStream;
            } catch (audioError) {
                throw new Error('No camera or microphone found. Please connect a device and reload.');
            }
        } else if (error.name === 'NotReadableError') {
            throw new Error('Camera/microphone is already in use by another application.');
        } else if (error.name === 'OverconstrainedError') {
            // Try with relaxed constraints
            try {
                console.log('Constraints too strict, trying with relaxed settings');
                this.localStream = await navigator.mediaDevices.getUserMedia({
                    audio: true,
                    video: true
                });
                this.displayLocalVideo();
                return this.localStream;
            } catch (fallbackError) {
                throw new Error('Failed to access camera/microphone with any settings.');
            }
        } else {
            throw new Error('Failed to access camera/microphone: ' + error.message);
        }
    }
};

/**
 * Display local video stream
 * Implements: Display local video streams
 */
VideoCallInterface.prototype.displayLocalVideo = function() {
    const localVideo = document.getElementById('local-video');
    if (localVideo && this.localStream) {
        localVideo.srcObject = this.localStream;
        localVideo.muted = true; // Mute local audio to prevent feedback
        localVideo.play().catch(error => {
            console.error('Error playing local video:', error);
        });
        
        // Ensure placeholder is hidden when video is displayed
        this.showLocalVideoPlaceholder(false);
    }
};

/**
 * Display remote video stream
 * Implements: Display remote video streams
 */
VideoCallInterface.prototype.displayRemoteVideo = function(peerId, stream) {
    let videoContainer = document.querySelector(`[data-peer-id="${peerId}"]`);
    
    if (!videoContainer) {
        // Create new video container
        videoContainer = this.createVideoContainer(peerId);
    }
    
    const videoElement = videoContainer.querySelector('video');
    if (videoElement) {
        videoElement.srcObject = stream;
        videoElement.play().catch(error => {
            console.error('Error playing remote video:', error);
        });
        
        // Check if video track is enabled
        const videoTrack = stream.getVideoTracks()[0];
        if (videoTrack) {
            const participant = this.participants.get(peerId);
            const videoEnabled = participant ? participant.videoEnabled : true;
            this.showVideoPlaceholder(peerId, !videoEnabled);
        }
    }
    
    // Update video grid layout
    this.updateVideoGrid();
};

/**
 * Create video container for a participant
 * Implements: Add placeholder for disabled cameras
 */
VideoCallInterface.prototype.createVideoContainer = function(peerId) {
    const participant = this.participants.get(peerId);
    const userName = participant ? participant.userName : 'Unknown';
    
    const container = document.createElement('div');
    container.className = 'video-container';
    container.setAttribute('data-peer-id', peerId);
    
    container.innerHTML = `
        <video autoplay playsinline></video>
        <div class="video-placeholder" style="display: none;">
            <div class="avatar">${this.getInitials(userName)}</div>
        </div>
        <div class="video-overlay">
            <div class="participant-name">${userName}</div>
            <div class="connection-quality quality-unknown"></div>
            <div class="audio-indicator" style="display: none;">
                <i class="fas fa-microphone"></i>
            </div>
        </div>
    `;
    
    const videoGrid = document.getElementById('video-grid');
    if (videoGrid) {
        videoGrid.appendChild(container);
    }
    
    return container;
};

/**
 * Remove remote video
 */
VideoCallInterface.prototype.removeRemoteVideo = function(peerId) {
    const videoContainer = document.querySelector(`[data-peer-id="${peerId}"]`);
    if (videoContainer) {
        videoContainer.remove();
    }
    
    // Update video grid layout
    this.updateVideoGrid();
};

/**
 * Update video grid layout based on number of participants
 * Implements: Responsive video grid layout for multiple participants
 */
VideoCallInterface.prototype.updateVideoGrid = function() {
    const videoGrid = document.getElementById('video-grid');
    if (!videoGrid) return;
    
    const totalVideos = videoGrid.children.length;
    
    // Remove existing grid classes
    videoGrid.className = 'video-grid';
    
    // Check if anyone is screen sharing
    const screenSharingActive = Array.from(this.participants.values()).some(p => p.screenSharing) || this.screenSharing;
    
    if (screenSharingActive) {
        // Optimize layout for screen sharing (larger main view)
        videoGrid.classList.add('grid-screen-share');
    } else {
        // Add appropriate grid class based on participant count
        if (totalVideos === 1) {
            videoGrid.classList.add('grid-1');
        } else if (totalVideos === 2) {
            videoGrid.classList.add('grid-2');
        } else if (totalVideos <= 4) {
            videoGrid.classList.add('grid-4');
        } else if (totalVideos <= 6) {
            videoGrid.classList.add('grid-6');
        } else if (totalVideos <= 9) {
            videoGrid.classList.add('grid-9');
        } else {
            videoGrid.classList.add('grid-many');
        }
    }
};

/**
 * Show video placeholder when camera is disabled
 * Implements: Add placeholder for disabled cameras
 */
VideoCallInterface.prototype.showVideoPlaceholder = function(peerId, show) {
    const container = document.querySelector(`[data-peer-id="${peerId}"]`);
    if (!container) return;
    
    const video = container.querySelector('video');
    const placeholder = container.querySelector('.video-placeholder');
    
    if (show) {
        video.style.display = 'none';
        placeholder.style.display = 'flex';
    } else {
        video.style.display = 'block';
        placeholder.style.display = 'none';
    }
};

/**
 * Handle media state change from other participants
 */
VideoCallInterface.prototype.handleMediaStateChange = function(message) {
    const peerId = message.user_id;
    const participant = this.participants.get(peerId);
    
    if (participant) {
        participant.audioEnabled = message.audio_enabled;
        participant.videoEnabled = message.video_enabled;
        
        // Update video placeholder visibility
        this.showVideoPlaceholder(peerId, !message.video_enabled);
        
        // Update audio indicator visibility
        const container = document.querySelector(`[data-peer-id="${peerId}"]`);
        if (container) {
            const audioIndicator = container.querySelector('.audio-indicator');
            if (audioIndicator && !message.audio_enabled) {
                audioIndicator.style.display = 'none';
            }
        }
        
        // Update participant list
        this.updateParticipantsList();
    }
};

/**
 * Get initials from name for avatar
 */
VideoCallInterface.prototype.getInitials = function(name) {
    if (!name) return '?';
    
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    } else {
        return name.substring(0, 2).toUpperCase();
    }
};

/**
 * Replace video track (used for screen sharing)
 */
VideoCallInterface.prototype.replaceVideoTrack = async function(newTrack) {
    const promises = [];
    
    this.peerConnections.forEach((pc, peerId) => {
        const sender = pc.getSenders().find(s => s.track && s.track.kind === 'video');
        if (sender) {
            promises.push(sender.replaceTrack(newTrack));
        }
    });
    
    await Promise.all(promises);
};


// ============================================================================
// Media Control UI
// ============================================================================

/**
 * Set up UI event listeners
 */
VideoCallInterface.prototype.setupUIListeners = function() {
    // Audio toggle button
    const audioBtn = document.getElementById('toggle-audio');
    if (audioBtn) {
        audioBtn.addEventListener('click', () => this.toggleAudio());
    }
    
    // Video toggle button
    const videoBtn = document.getElementById('toggle-video');
    if (videoBtn) {
        videoBtn.addEventListener('click', () => this.toggleVideo());
    }
    
    // Screen share button
    const screenBtn = document.getElementById('toggle-screen-share');
    if (screenBtn) {
        screenBtn.addEventListener('click', () => this.toggleScreenShare());
    }
    
    // Leave session button
    const leaveBtn = document.getElementById('leave-session');
    if (leaveBtn) {
        leaveBtn.addEventListener('click', () => this.leaveSession());
    }
    
    // Handle page unload
    window.addEventListener('beforeunload', () => {
        this.cleanup();
    });
    
    // Set up keyboard shortcuts
    this.setupKeyboardShortcuts();
};

/**
 * Set up keyboard shortcuts for media controls
 */
VideoCallInterface.prototype.setupKeyboardShortcuts = function() {
    document.addEventListener('keydown', (event) => {
        // Ignore if user is typing in an input field
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }
        
        // Ctrl/Cmd + D: Toggle audio
        if ((event.ctrlKey || event.metaKey) && event.key === 'd') {
            event.preventDefault();
            this.toggleAudio();
        }
        
        // Ctrl/Cmd + E: Toggle video
        if ((event.ctrlKey || event.metaKey) && event.key === 'e') {
            event.preventDefault();
            this.toggleVideo();
        }
        
        // Ctrl/Cmd + S: Toggle screen share
        if ((event.ctrlKey || event.metaKey) && event.key === 's') {
            event.preventDefault();
            this.toggleScreenShare();
        }
        
        // Ctrl/Cmd + P: Toggle participants list
        if ((event.ctrlKey || event.metaKey) && event.key === 'p') {
            event.preventDefault();
            this.toggleParticipantList();
        }
    });
};

/**
 * Toggle audio (mute/unmute)
 */
VideoCallInterface.prototype.toggleAudio = function() {
    if (!this.localStream) return;
    
    const audioTrack = this.localStream.getAudioTracks()[0];
    if (audioTrack) {
        this.audioEnabled = !this.audioEnabled;
        audioTrack.enabled = this.audioEnabled;
        
        // Update UI
        this.updateAudioButton();
        
        // Notify other participants
        this.sendWebSocketMessage({
            type: 'media_state_change',
            audio_enabled: this.audioEnabled,
            video_enabled: this.videoEnabled
        });
        
        console.log('Audio', this.audioEnabled ? 'enabled' : 'disabled');
    }
};

/**
 * Toggle video (enable/disable camera)
 */
VideoCallInterface.prototype.toggleVideo = function() {
    if (!this.localStream) return;
    
    const videoTrack = this.localStream.getVideoTracks()[0];
    if (videoTrack) {
        this.videoEnabled = !this.videoEnabled;
        videoTrack.enabled = this.videoEnabled;
        
        // Update UI
        this.updateVideoButton();
        this.showLocalVideoPlaceholder(!this.videoEnabled);
        
        // Notify other participants
        this.sendWebSocketMessage({
            type: 'media_state_change',
            audio_enabled: this.audioEnabled,
            video_enabled: this.videoEnabled
        });
        
        console.log('Video', this.videoEnabled ? 'enabled' : 'disabled');
    }
};

/**
 * Toggle screen sharing
 */
VideoCallInterface.prototype.toggleScreenShare = async function() {
    const btn = document.getElementById('toggle-screen-share');
    
    // Prevent multiple clicks
    if (btn && btn.classList.contains('loading')) {
        return;
    }
    
    // Add loading state
    if (btn) btn.classList.add('loading');
    
    try {
        if (this.screenSharing) {
            await this.stopScreenShare();
        } else {
            await this.startScreenShare();
        }
    } finally {
        // Remove loading state
        if (btn) btn.classList.remove('loading');
    }
};

/**
 * Start screen sharing
 */
VideoCallInterface.prototype.startScreenShare = async function() {
    try {
        // Get screen stream
        this.screenStream = await navigator.mediaDevices.getDisplayMedia({
            video: {
                cursor: 'always'
            },
            audio: false
        });
        
        const screenTrack = this.screenStream.getVideoTracks()[0];
        
        // Handle screen share stop (when user clicks browser's stop button)
        screenTrack.onended = () => {
            this.stopScreenShare();
        };
        
        // Replace video track with screen track
        await this.replaceVideoTrack(screenTrack);
        
        this.screenSharing = true;
        
        // Update UI
        this.updateScreenShareButton();
        
        // Notify other participants
        this.sendWebSocketMessage({
            type: 'screen_share_start'
        });
        
        console.log('Screen sharing started');
    } catch (error) {
        console.error('Error starting screen share:', error);
        
        if (error.name !== 'NotAllowedError') {
            this.showError('Failed to start screen sharing: ' + error.message);
        }
    }
};

/**
 * Stop screen sharing
 */
VideoCallInterface.prototype.stopScreenShare = async function() {
    if (!this.screenSharing) return;
    
    try {
        // Stop screen stream
        if (this.screenStream) {
            this.screenStream.getTracks().forEach(track => track.stop());
            this.screenStream = null;
        }
        
        // Replace with camera track
        const videoTrack = this.localStream.getVideoTracks()[0];
        await this.replaceVideoTrack(videoTrack);
        
        this.screenSharing = false;
        
        // Update UI
        this.updateScreenShareButton();
        
        // Notify other participants
        this.sendWebSocketMessage({
            type: 'screen_share_stop'
        });
        
        console.log('Screen sharing stopped');
    } catch (error) {
        console.error('Error stopping screen share:', error);
    }
};

/**
 * Handle screen share start from other participant
 */
VideoCallInterface.prototype.handleScreenShareStart = function(message) {
    const peerId = message.user_id;
    const participant = this.participants.get(peerId);
    
    if (participant) {
        participant.screenSharing = true;
        this.updateParticipantsList();
        
        // Show notification
        this.showNotification(`${participant.userName} is sharing their screen`);
    }
};

/**
 * Handle screen share stop from other participant
 */
VideoCallInterface.prototype.handleScreenShareStop = function(message) {
    const peerId = message.user_id;
    const participant = this.participants.get(peerId);
    
    if (participant) {
        participant.screenSharing = false;
        this.updateParticipantsList();
    }
};

/**
 * Leave the video session
 */
VideoCallInterface.prototype.leaveSession = function() {
    if (confirm('Are you sure you want to leave this session?')) {
        // Send leave message
        this.sendWebSocketMessage({
            type: 'leave_session'
        });
        
        // Clean up
        this.cleanup();
        
        // Redirect to session list or dashboard
        window.location.href = '/video/sessions/';
    }
};

/**
 * Update audio button UI
 */
VideoCallInterface.prototype.updateAudioButton = function() {
    const btn = document.getElementById('toggle-audio');
    if (!btn) return;
    
    const icon = btn.querySelector('i');
    const text = btn.querySelector('.btn-text');
    
    if (this.audioEnabled) {
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-secondary');
        btn.classList.remove('active');
        if (icon) icon.className = 'fas fa-microphone';
        if (text) text.textContent = 'Mute';
        btn.title = 'Mute microphone';
    } else {
        btn.classList.remove('btn-secondary');
        btn.classList.add('btn-danger');
        btn.classList.add('active');
        if (icon) icon.className = 'fas fa-microphone-slash';
        if (text) text.textContent = 'Unmute';
        btn.title = 'Unmute microphone';
    }
};

/**
 * Update video button UI
 */
VideoCallInterface.prototype.updateVideoButton = function() {
    const btn = document.getElementById('toggle-video');
    if (!btn) return;
    
    const icon = btn.querySelector('i');
    const text = btn.querySelector('.btn-text');
    
    if (this.videoEnabled) {
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-secondary');
        btn.classList.remove('active');
        if (icon) icon.className = 'fas fa-video';
        if (text) text.textContent = 'Stop Video';
        btn.title = 'Turn off camera';
    } else {
        btn.classList.remove('btn-secondary');
        btn.classList.add('btn-danger');
        btn.classList.add('active');
        if (icon) icon.className = 'fas fa-video-slash';
        if (text) text.textContent = 'Start Video';
        btn.title = 'Turn on camera';
    }
};

/**
 * Update screen share button UI
 */
VideoCallInterface.prototype.updateScreenShareButton = function() {
    const btn = document.getElementById('toggle-screen-share');
    if (!btn) return;
    
    const icon = btn.querySelector('i');
    const text = btn.querySelector('.btn-text');
    
    if (this.screenSharing) {
        btn.classList.remove('btn-secondary');
        btn.classList.add('btn-primary');
        btn.classList.add('active');
        if (icon) icon.className = 'fas fa-stop-circle';
        if (text) text.textContent = 'Stop Sharing';
        btn.title = 'Stop sharing your screen';
    } else {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-secondary');
        btn.classList.remove('active');
        if (icon) icon.className = 'fas fa-desktop';
        if (text) text.textContent = 'Share Screen';
        btn.title = 'Share your screen';
    }
};

/**
 * Show local video placeholder
 */
VideoCallInterface.prototype.showLocalVideoPlaceholder = function(show) {
    const localVideo = document.getElementById('local-video');
    const placeholder = document.getElementById('local-video-placeholder');
    
    if (show) {
        if (localVideo) localVideo.style.display = 'none';
        if (placeholder) placeholder.style.display = 'flex';
    } else {
        if (localVideo) localVideo.style.display = 'block';
        if (placeholder) placeholder.style.display = 'none';
    }
};

/**
 * Show notification
 */
VideoCallInterface.prototype.showNotification = function(message) {
    const notification = document.createElement('div');
    notification.className = 'video-notification';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
};


// ============================================================================
// Participant List and Engagement Indicators
// ============================================================================

/**
 * Update participants list UI
 */
VideoCallInterface.prototype.updateParticipantsList = function() {
    const participantsList = document.getElementById('participants-list');
    if (!participantsList) return;
    
    // Clear existing list
    participantsList.innerHTML = '';
    
    // Add self first
    const selfItem = this.createParticipantListItem({
        userId: this.userId,
        userName: this.userName + ' (You)',
        audioEnabled: this.audioEnabled,
        videoEnabled: this.videoEnabled,
        screenSharing: this.screenSharing,
        joinedAt: new Date(),
        isSelf: true
    });
    participantsList.appendChild(selfItem);
    
    // Add other participants
    this.participants.forEach((participant, peerId) => {
        const item = this.createParticipantListItem(participant);
        participantsList.appendChild(item);
    });
    
    // Update participant count
    this.updateParticipantCount();
};

/**
 * Create participant list item
 */
VideoCallInterface.prototype.createParticipantListItem = function(participant) {
    const item = document.createElement('div');
    item.className = 'participant-item';
    item.setAttribute('data-user-id', participant.userId);
    
    const now = new Date();
    const joinDuration = Math.floor((now - participant.joinedAt) / 1000 / 60); // minutes
    const joinTime = this.formatJoinTime(joinDuration);
    
    // Check if idle (more than 5 minutes without activity)
    const isIdle = participant.lastActivity && 
                   (now - participant.lastActivity) > 5 * 60 * 1000;
    
    item.innerHTML = `
        <div class="participant-avatar">
            ${this.getInitials(participant.userName)}
        </div>
        <div class="participant-info">
            <div class="participant-name">
                ${participant.userName}
                ${participant.screenSharing ? '<i class="fas fa-desktop text-primary" title="Sharing screen"></i>' : ''}
                ${isIdle ? '<span class="idle-badge">Idle</span>' : ''}
            </div>
            <div class="participant-meta">
                <span class="join-time">${joinTime}</span>
            </div>
        </div>
        <div class="participant-status">
            <div class="media-indicators">
                <i class="fas fa-microphone${participant.audioEnabled ? '' : '-slash'} ${participant.audioEnabled ? 'text-success' : 'text-muted'}" 
                   title="${participant.audioEnabled ? 'Audio on' : 'Audio off'}"></i>
                <i class="fas fa-video${participant.videoEnabled ? '' : '-slash'} ${participant.videoEnabled ? 'text-success' : 'text-muted'}" 
                   title="${participant.videoEnabled ? 'Video on' : 'Video off'}"></i>
            </div>
            <div class="speaking-indicator" style="display: none;">
                <i class="fas fa-volume-up"></i>
            </div>
        </div>
    `;
    
    return item;
};

/**
 * Format join time
 */
VideoCallInterface.prototype.formatJoinTime = function(minutes) {
    if (minutes < 1) {
        return 'Just joined';
    } else if (minutes === 1) {
        return '1 minute ago';
    } else if (minutes < 60) {
        return `${minutes} minutes ago`;
    } else {
        const hours = Math.floor(minutes / 60);
        return hours === 1 ? '1 hour ago' : `${hours} hours ago`;
    }
};

/**
 * Update participant count
 */
VideoCallInterface.prototype.updateParticipantCount = function() {
    const countElement = document.getElementById('participant-count');
    if (countElement) {
        const total = this.participants.size + 1; // +1 for self
        countElement.textContent = total;
    }
};

/**
 * Show speaking indicator for a participant
 */
VideoCallInterface.prototype.showSpeakingIndicator = function(peerId, isSpeaking) {
    // Update in video grid
    const videoContainer = document.querySelector(`[data-peer-id="${peerId}"]`);
    if (videoContainer) {
        const audioIndicator = videoContainer.querySelector('.audio-indicator');
        if (audioIndicator) {
            audioIndicator.style.display = isSpeaking ? 'block' : 'none';
        }
    }
    
    // Update in participant list
    const participantItem = document.querySelector(`.participant-item[data-user-id="${peerId}"]`);
    if (participantItem) {
        const speakingIndicator = participantItem.querySelector('.speaking-indicator');
        if (speakingIndicator) {
            speakingIndicator.style.display = isSpeaking ? 'block' : 'none';
        }
    }
};

/**
 * Monitor audio levels to detect speaking
 */
VideoCallInterface.prototype.startAudioLevelMonitoring = function() {
    // Monitor local audio
    if (this.localStream) {
        this.monitorAudioLevel(this.localStream, this.userId);
    }
    
    // Monitor remote audio
    this.remoteStreams.forEach((stream, peerId) => {
        this.monitorAudioLevel(stream, peerId);
    });
};

/**
 * Monitor audio level for a stream
 */
VideoCallInterface.prototype.monitorAudioLevel = function(stream, userId) {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const analyser = audioContext.createAnalyser();
        const microphone = audioContext.createMediaStreamSource(stream);
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        
        microphone.connect(analyser);
        analyser.fftSize = 256;
        
        const checkAudioLevel = () => {
            analyser.getByteFrequencyData(dataArray);
            
            // Calculate average volume
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i];
            }
            const average = sum / dataArray.length;
            
            // Threshold for speaking detection
            const isSpeaking = average > 20;
            
            this.showSpeakingIndicator(userId, isSpeaking);
            
            // Continue monitoring
            requestAnimationFrame(checkAudioLevel);
        };
        
        checkAudioLevel();
    } catch (error) {
        console.error('Error monitoring audio level:', error);
    }
};

/**
 * Mark participant as active (for idle detection)
 */
VideoCallInterface.prototype.markParticipantActive = function(peerId) {
    const participant = this.participants.get(peerId);
    if (participant) {
        participant.lastActivity = new Date();
        this.updateParticipantsList();
    }
};

/**
 * Start idle detection
 */
VideoCallInterface.prototype.startIdleDetection = function() {
    // Check for idle participants every minute
    setInterval(() => {
        this.updateParticipantsList();
    }, 60000);
};

/**
 * Toggle participant list visibility
 */
VideoCallInterface.prototype.toggleParticipantList = function() {
    const sidebar = document.getElementById('participants-sidebar');
    if (sidebar) {
        sidebar.classList.toggle('hidden');
    }
};

/**
 * Initialize engagement monitoring
 */
VideoCallInterface.prototype.initializeEngagementMonitoring = function() {
    // Start audio level monitoring for speaking indicators
    this.startAudioLevelMonitoring();
    
    // Start idle detection
    this.startIdleDetection();
    
    // Update participant list periodically
    setInterval(() => {
        this.updateParticipantsList();
    }, 30000); // Every 30 seconds
};

/**
 * Update overall connection quality indicator in control bar
 */
VideoCallInterface.prototype.updateOverallConnectionQuality = function() {
    const indicator = document.getElementById('connection-quality-indicator');
    if (!indicator) return;
    
    // Calculate overall quality based on all connections
    let worstQuality = 'excellent';
    let qualityScore = 4; // excellent = 4, good = 3, fair = 2, poor = 1
    
    this.connectionStats.forEach((stats, peerId) => {
        const quality = stats.quality;
        let score = 4;
        
        if (quality === 'good') score = 3;
        else if (quality === 'fair') score = 2;
        else if (quality === 'poor') score = 1;
        else if (quality === 'unknown') score = 2;
        
        if (score < qualityScore) {
            qualityScore = score;
            worstQuality = quality;
        }
    });
    
    // If no connections yet, show connecting state
    if (this.peerConnections.size === 0) {
        worstQuality = 'unknown';
        qualityScore = 0;
    }
    
    // Update indicator class
    indicator.className = `connection-quality-display quality-${worstQuality}`;
    
    // Update quality bars
    const bars = indicator.querySelectorAll('.quality-bar');
    bars.forEach((bar, index) => {
        if (index < qualityScore) {
            bar.classList.add('active');
        } else {
            bar.classList.remove('active');
        }
    });
    
    // Update text
    const textElement = indicator.querySelector('.quality-text');
    if (textElement) {
        const qualityLabels = {
            'excellent': 'Excellent',
            'good': 'Good',
            'fair': 'Fair',
            'poor': 'Poor',
            'unknown': 'Connecting...'
        };
        textElement.textContent = qualityLabels[worstQuality] || 'Unknown';
    }
    
    // Update tooltip
    indicator.title = `Connection Quality: ${worstQuality}`;
};

/**
 * Update connection quality display when connection state changes
 */
VideoCallInterface.prototype.updateConnectionStateDisplay = function(state) {
    const indicator = document.getElementById('connection-quality-indicator');
    if (!indicator) return;
    
    const textElement = indicator.querySelector('.quality-text');
    const bars = indicator.querySelectorAll('.quality-bar');
    
    switch (state) {
        case 'connecting':
            indicator.className = 'connection-quality-display quality-unknown';
            if (textElement) textElement.textContent = 'Connecting...';
            bars.forEach(bar => bar.classList.remove('active'));
            break;
            
        case 'connected':
            // Will be updated by connection stats
            this.updateOverallConnectionQuality();
            break;
            
        case 'disconnected':
            indicator.className = 'connection-quality-display quality-poor';
            if (textElement) textElement.textContent = 'Disconnected';
            bars.forEach((bar, index) => {
                bar.classList.toggle('active', index === 0);
            });
            break;
            
        case 'failed':
            indicator.className = 'connection-quality-display quality-poor';
            if (textElement) textElement.textContent = 'Failed';
            bars.forEach(bar => bar.classList.remove('active'));
            break;
    }
};
