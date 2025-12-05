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
        
        // Recording state
        this.isRecording = false;
        this.mediaRecorder = null;
        this.recordedChunks = [];
        this.recordingStartTime = null;
        
        // Connection quality monitoring
        this.connectionStats = new Map(); // userId -> stats
        this.statsInterval = null;
        
        // ICE servers configuration (will be loaded from server)
        this.iceServers = [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
            { urls: 'stun:stun2.l.google.com:19302' }
        ];
        
        // Video chat settings
        this.videoSettings = {
            maxParticipants: 30,
            sessionTimeout: 3600,
            recordingEnabled: true,
            screenShareEnabled: true
        };
        
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
            // Initialize tracking variables
            this.reconnectionAttempts = new Map();
            this.audioOnlySuggested = false;
            
            // Load ICE server configuration from server
            await this.loadICEServerConfiguration();
            
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
            
            // Start adaptive quality monitoring
            // Requirements: 9.1 - Adjust video resolution based on bandwidth
            this.startAdaptiveQualityMonitoring();
            
            // Initialize engagement monitoring (speaking indicators, idle detection)
            this.initializeEngagementMonitoring();
            
            // Initialize participant list
            this.updateParticipantsList();
            
            console.log('Video call interface initialized');
        } catch (error) {
            console.error('Failed to initialize video call:', error);
            this.showError('Failed to initialize video call: ' + error.message);
        }
    }
    
    /**
     * Load ICE server configuration from the server
     * Requirements: 1.3, 4.3, 9.1 - Configure STUN/TURN servers for WebRTC connections
     */
    async loadICEServerConfiguration() {
        try {
            const response = await fetch('/video-chat/api/ice-servers/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error('Failed to load ICE server configuration');
            }
            
            const data = await response.json();
            
            // Update ICE servers configuration
            if (data.iceServers && data.iceServers.length > 0) {
                this.iceServers = data.iceServers;
                console.log('Loaded ICE servers configuration:', this.iceServers.length, 'servers');
            }
            
            // Update video chat settings
            if (data.maxParticipants) {
                this.videoSettings.maxParticipants = data.maxParticipants;
            }
            if (data.sessionTimeout) {
                this.videoSettings.sessionTimeout = data.sessionTimeout;
            }
            if (typeof data.recordingEnabled !== 'undefined') {
                this.videoSettings.recordingEnabled = data.recordingEnabled;
            }
            if (typeof data.screenShareEnabled !== 'undefined') {
                this.videoSettings.screenShareEnabled = data.screenShareEnabled;
            }
            
            console.log('Video chat settings loaded:', this.videoSettings);
        } catch (error) {
            console.error('Failed to load ICE server configuration:', error);
            console.log('Using default STUN servers');
            // Continue with default STUN servers if loading fails
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
                    
                case 'recording_started':
                    this.handleRecordingStarted(message);
                    break;
                    
                case 'recording_stopped':
                    this.handleRecordingStopped(message);
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
            screenSharing: false,
            joinedAt: new Date(),
            lastActivity: new Date()
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
                    screenSharing: false,
                    joinedAt: new Date(participant.joined_at),
                    lastActivity: new Date()
                });
            }
        });
        
        this.updateParticipantsList();
    }

    
    /**
     * Restart ICE connection
     * Requirements: 9.2, 9.3 - Implement automatic reconnection on disconnect
     */
    async restartICE(peerId) {
        console.log('Restarting ICE for:', peerId);
        
        const pc = this.peerConnections.get(peerId);
        if (pc) {
            try {
                // Track reconnection attempts
                if (!this.reconnectionAttempts) {
                    this.reconnectionAttempts = new Map();
                }
                
                const attempts = this.reconnectionAttempts.get(peerId) || 0;
                this.reconnectionAttempts.set(peerId, attempts + 1);
                
                // Show reconnecting indicator
                this.showReconnectingIndicator(peerId, true);
                
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
                
                // Set timeout for reconnection
                setTimeout(() => {
                    if (pc.connectionState !== 'connected') {
                        console.log('Reconnection timeout, trying again...');
                        if (attempts < 3) {
                            this.restartICE(peerId);
                        } else {
                            // After 3 attempts, suggest audio-only mode
                            this.showReconnectingIndicator(peerId, false);
                            this.suggestAudioOnlyMode(peerId);
                        }
                    } else {
                        // Successfully reconnected
                        this.reconnectionAttempts.set(peerId, 0);
                        this.showReconnectingIndicator(peerId, false);
                        this.showNotification('Connection restored');
                    }
                }, 10000); // 10 second timeout
                
            } catch (error) {
                console.error('Error restarting ICE:', error);
                this.showReconnectingIndicator(peerId, false);
            }
        }
    }
    
    /**
     * Show/hide reconnecting indicator for a peer
     * Requirements: 9.2, 9.3 - Visual feedback during reconnection
     */
    showReconnectingIndicator(peerId, show) {
        const container = document.querySelector(`[data-peer-id="${peerId}"]`);
        if (!container) return;
        
        let indicator = container.querySelector('.reconnecting-indicator');
        
        if (show && !indicator) {
            indicator = document.createElement('div');
            indicator.className = 'reconnecting-indicator';
            indicator.innerHTML = `
                <div class="spinner"></div>
                <span>Reconnecting...</span>
            `;
            container.appendChild(indicator);
        }
        
        if (indicator) {
            indicator.style.display = show ? 'flex' : 'none';
        }
    }
    
    /**
     * Adjust video resolution based on bandwidth
     * Requirements: 9.1 - Adjust video resolution based on bandwidth
     */
    async adjustVideoQuality(targetBitrate) {
        if (!this.localStream) return;
        
        const videoTrack = this.localStream.getVideoTracks()[0];
        if (!videoTrack) return;
        
        try {
            // Determine appropriate resolution based on target bitrate
            let constraints;
            
            if (targetBitrate < 500000) { // < 500 kbps
                // Low quality: 320x240 @ 15fps
                constraints = {
                    width: { ideal: 320 },
                    height: { ideal: 240 },
                    frameRate: { ideal: 15 }
                };
                console.log('Adjusting to low quality (320x240)');
            } else if (targetBitrate < 1000000) { // < 1 Mbps
                // Medium quality: 640x480 @ 24fps
                constraints = {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    frameRate: { ideal: 24 }
                };
                console.log('Adjusting to medium quality (640x480)');
            } else if (targetBitrate < 2000000) { // < 2 Mbps
                // High quality: 1280x720 @ 30fps
                constraints = {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    frameRate: { ideal: 30 }
                };
                console.log('Adjusting to high quality (1280x720)');
            } else {
                // Full HD: 1920x1080 @ 30fps
                constraints = {
                    width: { ideal: 1920 },
                    height: { ideal: 1080 },
                    frameRate: { ideal: 30 }
                };
                console.log('Adjusting to full HD (1920x1080)');
            }
            
            // Apply constraints to video track
            await videoTrack.applyConstraints(constraints);
            
            // Also adjust bitrate for all peer connections
            this.peerConnections.forEach((pc, peerId) => {
                const sender = pc.getSenders().find(s => s.track && s.track.kind === 'video');
                if (sender) {
                    const parameters = sender.getParameters();
                    if (!parameters.encodings) {
                        parameters.encodings = [{}];
                    }
                    
                    // Set max bitrate
                    parameters.encodings[0].maxBitrate = targetBitrate;
                    
                    sender.setParameters(parameters).catch(error => {
                        console.error('Error setting bitrate:', error);
                    });
                }
            });
            
        } catch (error) {
            console.error('Error adjusting video quality:', error);
        }
    }
    
    /**
     * Monitor bandwidth and adjust quality automatically
     * Requirements: 9.1 - Adjust video resolution based on bandwidth
     */
    startAdaptiveQualityMonitoring() {
        // Check bandwidth every 5 seconds and adjust quality
        setInterval(() => {
            let lowestBitrate = Infinity;
            
            // Find the lowest available bitrate among all connections
            this.connectionStats.forEach((stats, peerId) => {
                if (stats.current && stats.current.availableOutgoingBitrate > 0) {
                    lowestBitrate = Math.min(lowestBitrate, stats.current.availableOutgoingBitrate);
                }
            });
            
            // Adjust quality if we have valid bitrate data
            if (lowestBitrate !== Infinity && lowestBitrate > 0) {
                // Use 80% of available bitrate to leave headroom
                const targetBitrate = lowestBitrate * 0.8;
                this.adjustVideoQuality(targetBitrate);
            }
        }, 5000);
    }
    
    /**
     * Suggest audio-only mode to user
     * Requirements: 9.5 - Add audio-only fallback option
     */
    suggestAudioOnlyMode(peerId) {
        const participant = this.participants.get(peerId);
        const userName = participant ? participant.userName : 'this participant';
        
        // Check if we already suggested this
        if (this.audioOnlySuggested) return;
        this.audioOnlySuggested = true;
        
        // Show modal or notification with option to switch to audio-only
        const message = `Connection quality with ${userName} is very poor. Would you like to switch to audio-only mode?`;
        
        if (confirm(message)) {
            this.switchToAudioOnly();
        }
    }
    
    /**
     * Switch to audio-only mode
     * Requirements: 9.5 - Add audio-only fallback option
     */
    async switchToAudioOnly() {
        try {
            console.log('Switching to audio-only mode');
            
            // Disable local video
            if (this.localStream) {
                const videoTrack = this.localStream.getVideoTracks()[0];
                if (videoTrack) {
                    videoTrack.enabled = false;
                    this.videoEnabled = false;
                }
            }
            
            // Remove video tracks from all peer connections
            this.peerConnections.forEach((pc, peerId) => {
                const sender = pc.getSenders().find(s => s.track && s.track.kind === 'video');
                if (sender && sender.track) {
                    sender.track.enabled = false;
                }
            });
            
            // Update UI
            this.updateVideoButton();
            this.showLocalVideoPlaceholder(true);
            
            // Notify other participants
            this.sendWebSocketMessage({
                type: 'media_state_change',
                audio_enabled: this.audioEnabled,
                video_enabled: false
            });
            
            // Show notification
            this.showNotification('Switched to audio-only mode to improve connection quality');
            
            // Add audio-only indicator
            this.showAudioOnlyIndicator(true);
            
        } catch (error) {
            console.error('Error switching to audio-only mode:', error);
            this.showError('Failed to switch to audio-only mode');
        }
    }
    
    /**
     * Switch back to video mode
     * Requirements: 9.5 - Allow switching back from audio-only
     */
    async switchToVideoMode() {
        try {
            console.log('Switching back to video mode');
            
            // Enable local video
            if (this.localStream) {
                const videoTrack = this.localStream.getVideoTracks()[0];
                if (videoTrack) {
                    videoTrack.enabled = true;
                    this.videoEnabled = true;
                }
            }
            
            // Enable video tracks in all peer connections
            this.peerConnections.forEach((pc, peerId) => {
                const sender = pc.getSenders().find(s => s.track && s.track.kind === 'video');
                if (sender && sender.track) {
                    sender.track.enabled = true;
                }
            });
            
            // Update UI
            this.updateVideoButton();
            this.showLocalVideoPlaceholder(false);
            
            // Notify other participants
            this.sendWebSocketMessage({
                type: 'media_state_change',
                audio_enabled: this.audioEnabled,
                video_enabled: true
            });
            
            // Hide audio-only indicator
            this.showAudioOnlyIndicator(false);
            
            // Reset suggestion flag
            this.audioOnlySuggested = false;
            
        } catch (error) {
            console.error('Error switching to video mode:', error);
            this.showError('Failed to switch to video mode');
        }
    }
    
    /**
     * Show/hide audio-only mode indicator
     * Requirements: 9.5 - Visual indicator for audio-only mode
     */
    showAudioOnlyIndicator(show) {
        let indicator = document.getElementById('audio-only-indicator');
        
        if (show && !indicator) {
            indicator = document.createElement('div');
            indicator.id = 'audio-only-indicator';
            indicator.className = 'audio-only-indicator';
            indicator.innerHTML = `
                <i class="fas fa-volume-up"></i>
                <span>Audio-Only Mode</span>
                <button class="btn-switch-video" onclick="videoCall.switchToVideoMode()">
                    <i class="fas fa-video"></i> Enable Video
                </button>
            `;
            
            const controlBar = document.querySelector('.video-controls');
            if (controlBar) {
                controlBar.insertBefore(indicator, controlBar.firstChild);
            }
        }
        
        if (indicator) {
            indicator.style.display = show ? 'flex' : 'none';
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
     * Requirements: 9.1, 9.4 - Monitor RTCPeerConnection stats and calculate quality score
     */
    async getConnectionStats(peerId, pc) {
        try {
            const stats = await pc.getStats();
            let quality = 'unknown';
            let qualityScore = 0;
            
            // Collect detailed statistics
            const statsData = {
                bytesReceived: 0,
                bytesSent: 0,
                packetsLost: 0,
                packetsReceived: 0,
                jitter: 0,
                roundTripTime: 0,
                currentRoundTripTime: 0,
                availableOutgoingBitrate: 0,
                timestamp: Date.now()
            };
            
            stats.forEach(report => {
                // Inbound RTP stats (receiving)
                if (report.type === 'inbound-rtp') {
                    if (report.kind === 'video') {
                        statsData.bytesReceived = report.bytesReceived || 0;
                        statsData.packetsLost = report.packetsLost || 0;
                        statsData.packetsReceived = report.packetsReceived || 0;
                        statsData.jitter = report.jitter || 0;
                        statsData.framesDecoded = report.framesDecoded || 0;
                        statsData.framesDropped = report.framesDropped || 0;
                    }
                }
                
                // Outbound RTP stats (sending)
                if (report.type === 'outbound-rtp') {
                    if (report.kind === 'video') {
                        statsData.bytesSent = report.bytesSent || 0;
                        statsData.packetsSent = report.packetsSent || 0;
                    }
                }
                
                // Candidate pair stats (connection quality)
                if (report.type === 'candidate-pair' && report.state === 'succeeded') {
                    statsData.currentRoundTripTime = report.currentRoundTripTime || 0;
                    statsData.availableOutgoingBitrate = report.availableOutgoingBitrate || 0;
                }
                
                // Remote inbound RTP (for RTT)
                if (report.type === 'remote-inbound-rtp') {
                    statsData.roundTripTime = report.roundTripTime || 0;
                }
            });
            
            // Calculate quality score based on multiple factors
            qualityScore = this.calculateQualityScore(statsData, peerId);
            
            // Determine quality level
            if (qualityScore >= 80) {
                quality = 'excellent';
            } else if (qualityScore >= 60) {
                quality = 'good';
            } else if (qualityScore >= 40) {
                quality = 'fair';
            } else {
                quality = 'poor';
            }
            
            // Store stats with history for trend analysis
            const existingStats = this.connectionStats.get(peerId) || { history: [] };
            existingStats.quality = quality;
            existingStats.qualityScore = qualityScore;
            existingStats.current = statsData;
            existingStats.history = existingStats.history || [];
            existingStats.history.push({
                timestamp: statsData.timestamp,
                qualityScore: qualityScore,
                packetsLost: statsData.packetsLost,
                roundTripTime: statsData.roundTripTime
            });
            
            // Keep only last 30 data points (1 minute of history at 2s intervals)
            if (existingStats.history.length > 30) {
                existingStats.history.shift();
            }
            
            this.connectionStats.set(peerId, existingStats);
            this.updateConnectionQuality(peerId, quality);
            
            // Check if quality degradation requires action
            this.handleQualityChange(peerId, quality, qualityScore);
            
        } catch (error) {
            console.error('Error getting connection stats:', error);
        }
    }
    
    /**
     * Calculate connection quality score (0-100)
     * Requirements: 9.1, 9.4 - Calculate connection quality score
     */
    calculateQualityScore(statsData, peerId) {
        let score = 100;
        
        // Get previous stats for rate calculations
        const prevStats = this.connectionStats.get(peerId);
        const prevData = prevStats?.current;
        
        if (prevData) {
            // Calculate rates
            const timeDiff = (statsData.timestamp - prevData.timestamp) / 1000; // seconds
            
            if (timeDiff > 0) {
                // Packet loss rate (0-30 points penalty)
                const totalPackets = statsData.packetsReceived + statsData.packetsLost;
                const prevTotalPackets = prevData.packetsReceived + prevData.packetsLost;
                const packetsInPeriod = totalPackets - prevTotalPackets;
                const lostInPeriod = statsData.packetsLost - prevData.packetsLost;
                
                if (packetsInPeriod > 0) {
                    const lossRate = lostInPeriod / packetsInPeriod;
                    if (lossRate > 0.10) {
                        score -= 30; // >10% loss: severe penalty
                    } else if (lossRate > 0.05) {
                        score -= 20; // 5-10% loss: major penalty
                    } else if (lossRate > 0.02) {
                        score -= 10; // 2-5% loss: moderate penalty
                    } else if (lossRate > 0.01) {
                        score -= 5; // 1-2% loss: minor penalty
                    }
                }
                
                // Frame drop rate (0-20 points penalty)
                if (statsData.framesDecoded && statsData.framesDropped) {
                    const frameDropRate = statsData.framesDropped / statsData.framesDecoded;
                    if (frameDropRate > 0.10) {
                        score -= 20; // >10% drops: severe
                    } else if (frameDropRate > 0.05) {
                        score -= 15; // 5-10% drops: major
                    } else if (frameDropRate > 0.02) {
                        score -= 10; // 2-5% drops: moderate
                    } else if (frameDropRate > 0.01) {
                        score -= 5; // 1-2% drops: minor
                    }
                }
            }
        }
        
        // Round trip time (0-25 points penalty)
        const rtt = statsData.roundTripTime || statsData.currentRoundTripTime;
        if (rtt > 0) {
            if (rtt > 0.5) {
                score -= 25; // >500ms: severe latency
            } else if (rtt > 0.3) {
                score -= 20; // 300-500ms: high latency
            } else if (rtt > 0.15) {
                score -= 15; // 150-300ms: moderate latency
            } else if (rtt > 0.1) {
                score -= 10; // 100-150ms: noticeable latency
            } else if (rtt > 0.05) {
                score -= 5; // 50-100ms: slight latency
            }
        }
        
        // Jitter (0-15 points penalty)
        if (statsData.jitter > 0) {
            if (statsData.jitter > 0.05) {
                score -= 15; // >50ms jitter: severe
            } else if (statsData.jitter > 0.03) {
                score -= 10; // 30-50ms jitter: high
            } else if (statsData.jitter > 0.02) {
                score -= 5; // 20-30ms jitter: moderate
            }
        }
        
        // Bandwidth (0-10 points penalty)
        if (statsData.availableOutgoingBitrate > 0) {
            const bitrateMbps = statsData.availableOutgoingBitrate / 1000000;
            if (bitrateMbps < 0.5) {
                score -= 10; // <500kbps: very low
            } else if (bitrateMbps < 1.0) {
                score -= 5; // 500kbps-1Mbps: low
            }
        }
        
        // Ensure score is within bounds
        return Math.max(0, Math.min(100, score));
    }
    
    /**
     * Handle quality changes and trigger adaptive actions
     * Requirements: 9.1, 9.4 - Display quality indicator and handle degradation
     */
    handleQualityChange(peerId, quality, qualityScore) {
        const stats = this.connectionStats.get(peerId);
        if (!stats || !stats.history || stats.history.length < 3) {
            return; // Need more data points
        }
        
        // Check for sustained poor quality (3+ consecutive poor readings)
        const recentScores = stats.history.slice(-3).map(h => h.qualityScore);
        const avgRecentScore = recentScores.reduce((a, b) => a + b, 0) / recentScores.length;
        
        if (avgRecentScore < 40 && !stats.poorQualityNotified) {
            // Notify user of poor connection
            const participant = this.participants.get(peerId);
            const userName = participant ? participant.userName : 'A participant';
            this.showNotification(`Poor connection quality with ${userName}`);
            stats.poorQualityNotified = true;
            
            // Suggest audio-only mode if quality is very poor
            if (avgRecentScore < 25) {
                this.suggestAudioOnlyMode(peerId);
            }
        } else if (avgRecentScore >= 60 && stats.poorQualityNotified) {
            // Quality improved, reset notification flag
            stats.poorQualityNotified = false;
        }
    }
    
    /**
     * Update connection quality indicator
     * Requirements: 9.1, 9.4 - Display quality indicator to users
     */
    updateConnectionQuality(peerId, quality) {
        const qualityElement = document.querySelector(`[data-peer-id="${peerId}"] .connection-quality`);
        if (qualityElement) {
            qualityElement.className = `connection-quality quality-${quality}`;
            
            // Get detailed stats for tooltip
            const stats = this.connectionStats.get(peerId);
            let tooltipText = `Connection: ${quality}`;
            
            if (stats && stats.current) {
                const data = stats.current;
                const rtt = (data.roundTripTime || data.currentRoundTripTime) * 1000; // Convert to ms
                const lossRate = data.packetsReceived > 0 
                    ? ((data.packetsLost / (data.packetsReceived + data.packetsLost)) * 100).toFixed(1)
                    : 0;
                
                tooltipText += `\nQuality Score: ${stats.qualityScore}/100`;
                if (rtt > 0) tooltipText += `\nLatency: ${rtt.toFixed(0)}ms`;
                if (lossRate > 0) tooltipText += `\nPacket Loss: ${lossRate}%`;
                if (data.jitter > 0) tooltipText += `\nJitter: ${(data.jitter * 1000).toFixed(0)}ms`;
            }
            
            qualityElement.title = tooltipText;
            
            // Add visual indicator bars
            qualityElement.innerHTML = this.getQualityBarsHTML(quality);
        }
        
        // Update overall connection quality in control bar
        this.updateOverallConnectionQuality();
    }
    
    /**
     * Get HTML for quality indicator bars
     * Requirements: 9.4 - Display quality indicator to users
     */
    getQualityBarsHTML(quality) {
        const qualityLevels = {
            'excellent': 4,
            'good': 3,
            'fair': 2,
            'poor': 1,
            'unknown': 0
        };
        
        const level = qualityLevels[quality] || 0;
        let html = '<div class="quality-bars">';
        
        for (let i = 1; i <= 4; i++) {
            const activeClass = i <= level ? 'active' : '';
            html += `<div class="quality-bar ${activeClass}"></div>`;
        }
        
        html += '</div>';
        return html;
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
        
        // Clean up recording
        this.cleanupRecording();
        
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
    
    // Start monitoring audio level for this stream
    this.monitorAudioLevel(stream, peerId);
    
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
        <div class="screen-share-indicator" style="display: none;">
            <i class="fas fa-desktop"></i>
            <span>${userName} is sharing</span>
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
        
        // Mark participant as active
        this.markParticipantActive(peerId);
        
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
    
    // Recording button
    const recordBtn = document.getElementById('toggle-recording');
    if (recordBtn) {
        recordBtn.addEventListener('click', () => this.toggleRecording());
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
 * Requirements: 3.1, 3.2, 3.3
 */
VideoCallInterface.prototype.startScreenShare = async function() {
    try {
        // Get screen stream using getDisplayMedia API
        this.screenStream = await navigator.mediaDevices.getDisplayMedia({
            video: {
                cursor: 'always',
                displaySurface: 'monitor' // Prefer full screen
            },
            audio: false
        });
        
        const screenTrack = this.screenStream.getVideoTracks()[0];
        
        // Handle screen share stop event (when user clicks browser's stop button)
        screenTrack.onended = () => {
            console.log('Screen share ended by user');
            this.stopScreenShare();
        };
        
        // Replace video track with screen share track
        await this.replaceVideoTrack(screenTrack);
        
        this.screenSharing = true;
        
        // Update UI
        this.updateScreenShareButton();
        this.updateVideoGrid();
        this.showScreenShareIndicator(true);
        
        // Add screen sharing class to local video container
        const localContainer = document.querySelector('.video-container.local');
        if (localContainer) {
            localContainer.classList.add('screen-sharing');
        }
        
        // Notify other participants
        this.sendWebSocketMessage({
            type: 'screen_share_start'
        });
        
        // Show notification
        this.showNotification('You are now sharing your screen');
        
        console.log('Screen sharing started');
    } catch (error) {
        console.error('Error starting screen share:', error);
        
        if (error.name === 'NotAllowedError') {
            console.log('User cancelled screen sharing');
        } else if (error.name === 'NotFoundError') {
            this.showError('No screen available to share');
        } else if (error.name === 'NotSupportedError') {
            this.showError('Screen sharing is not supported in this browser');
        } else {
            this.showError('Failed to start screen sharing: ' + error.message);
        }
    }
};

/**
 * Stop screen sharing
 * Requirements: 3.1, 3.2, 3.3
 */
VideoCallInterface.prototype.stopScreenShare = async function() {
    if (!this.screenSharing) return;
    
    try {
        // Stop screen stream tracks
        if (this.screenStream) {
            this.screenStream.getTracks().forEach(track => track.stop());
            this.screenStream = null;
        }
        
        // Replace screen track with camera track
        const videoTrack = this.localStream.getVideoTracks()[0];
        if (videoTrack) {
            await this.replaceVideoTrack(videoTrack);
        }
        
        this.screenSharing = false;
        
        // Update UI
        this.updateScreenShareButton();
        this.updateVideoGrid();
        this.showScreenShareIndicator(false);
        
        // Remove screen sharing class from local video container
        const localContainer = document.querySelector('.video-container.local');
        if (localContainer) {
            localContainer.classList.remove('screen-sharing');
        }
        
        // Notify other participants
        this.sendWebSocketMessage({
            type: 'screen_share_stop'
        });
        
        console.log('Screen sharing stopped');
    } catch (error) {
        console.error('Error stopping screen share:', error);
        this.showError('Failed to stop screen sharing');
    }
};

/**
 * Handle screen share start from other participant
 * Requirements: 3.4, 3.5
 */
VideoCallInterface.prototype.handleScreenShareStart = function(message) {
    const peerId = message.user_id;
    const userName = message.username || 'Someone';
    const participant = this.participants.get(peerId);
    
    if (participant) {
        participant.screenSharing = true;
        
        // Mark participant as active
        this.markParticipantActive(peerId);
        
        // Update video grid layout for screen sharing
        this.updateVideoGrid();
        
        // Mark the video container as screen sharing
        const videoContainer = document.querySelector(`[data-peer-id="${peerId}"]`);
        if (videoContainer) {
            videoContainer.classList.add('screen-sharing');
        }
        
        // Add screen sharing indicator
        this.addRemoteScreenShareIndicator(peerId, participant.userName);
        
        this.updateParticipantsList();
        
        // Show notification
        this.showNotification(`${participant.userName} is sharing their screen`);
    }
};

/**
 * Handle screen share stop from other participant
 * Requirements: 3.4, 3.5
 */
VideoCallInterface.prototype.handleScreenShareStop = function(message) {
    const peerId = message.user_id;
    const participant = this.participants.get(peerId);
    
    if (participant) {
        participant.screenSharing = false;
        
        // Mark participant as active
        this.markParticipantActive(peerId);
        
        // Update video grid layout back to normal
        this.updateVideoGrid();
        
        // Remove screen sharing class from video container
        const videoContainer = document.querySelector(`[data-peer-id="${peerId}"]`);
        if (videoContainer) {
            videoContainer.classList.remove('screen-sharing');
        }
        
        // Remove screen sharing indicator
        this.removeRemoteScreenShareIndicator(peerId);
        
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

/**
 * Show/hide screen share indicator
 * Requirements: 3.4, 3.5
 */
VideoCallInterface.prototype.showScreenShareIndicator = function(show) {
    const indicator = document.querySelector('.video-container.local .screen-share-indicator');
    if (indicator) {
        indicator.style.display = show ? 'flex' : 'none';
    }
};

/**
 * Add screen sharing indicator to remote participant
 * Requirements: 3.4, 3.5
 */
VideoCallInterface.prototype.addRemoteScreenShareIndicator = function(peerId, userName) {
    const videoContainer = document.querySelector(`[data-peer-id="${peerId}"]`);
    if (!videoContainer) return;
    
    // Check if indicator already exists
    let indicator = videoContainer.querySelector('.screen-share-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'screen-share-indicator';
        indicator.innerHTML = `
            <i class="fas fa-desktop"></i>
            <span>${userName} is sharing</span>
        `;
        videoContainer.appendChild(indicator);
    }
    indicator.style.display = 'flex';
};

/**
 * Remove screen sharing indicator from remote participant
 * Requirements: 3.4, 3.5
 */
VideoCallInterface.prototype.removeRemoteScreenShareIndicator = function(peerId) {
    const videoContainer = document.querySelector(`[data-peer-id="${peerId}"]`);
    if (!videoContainer) return;
    
    const indicator = videoContainer.querySelector('.screen-share-indicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
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
                ${participant.screenSharing ? '<span class="screen-sharing-badge"><i class="fas fa-desktop"></i> Sharing</span>' : ''}
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


// ============================================================================
// Session Recording - Task 6.1 Implementation
// Requirements: 6.1, 6.2, 6.3
// ============================================================================

/**
 * Toggle recording (start/stop)
 */
VideoCallInterface.prototype.toggleRecording = async function() {
    const btn = document.getElementById('toggle-recording');
    
    // Prevent multiple clicks
    if (btn && btn.classList.contains('loading')) {
        return;
    }
    
    // Add loading state
    if (btn) btn.classList.add('loading');
    
    try {
        if (this.isRecording) {
            await this.stopRecording();
        } else {
            await this.startRecording();
        }
    } finally {
        // Remove loading state
        if (btn) btn.classList.remove('loading');
    }
};

/**
 * Start recording the session
 * Requirements: 6.1, 6.2, 6.3
 */
VideoCallInterface.prototype.startRecording = async function() {
    try {
        // Check if MediaRecorder is supported
        if (!window.MediaRecorder) {
            throw new Error('Recording is not supported in this browser');
        }
        
        // Create a composite stream with local audio/video
        const compositeStream = new MediaStream();
        
        // Add local stream tracks
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => {
                compositeStream.addTrack(track);
            });
        }
        
        // Note: In a real implementation, you would need to mix remote streams
        // This is a simplified version that records the local stream
        // For full session recording, consider server-side recording or more complex client mixing
        
        // Determine supported MIME type
        let mimeType = 'video/webm;codecs=vp9,opus';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
            mimeType = 'video/webm;codecs=vp8,opus';
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = 'video/webm';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = ''; // Let browser choose
                }
            }
        }
        
        // Create MediaRecorder
        const options = mimeType ? { mimeType } : {};
        this.mediaRecorder = new MediaRecorder(compositeStream, options);
        
        // Reset recorded chunks
        this.recordedChunks = [];
        this.recordingStartTime = new Date();
        
        // Handle data available event
        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                this.recordedChunks.push(event.data);
                
                // Send chunk to server via WebSocket
                this.sendRecordingChunk(event.data);
            }
        };
        
        // Handle recording stop event
        this.mediaRecorder.onstop = () => {
            console.log('Recording stopped, total chunks:', this.recordedChunks.length);
            
            // Notify server that recording is complete
            this.sendWebSocketMessage({
                type: 'recording_complete',
                chunk_count: this.recordedChunks.length,
                duration_seconds: this.recordingStartTime ? 
                    Math.floor((new Date() - this.recordingStartTime) / 1000) : 0
            });
        };
        
        // Handle errors
        this.mediaRecorder.onerror = (event) => {
            console.error('MediaRecorder error:', event.error);
            this.showError('Recording error: ' + event.error.message);
            this.stopRecording();
        };
        
        // Start recording with chunks every 5 seconds
        this.mediaRecorder.start(5000);
        
        this.isRecording = true;
        
        // Update UI
        this.updateRecordingButton();
        this.showRecordingIndicator(true);
        
        // Notify server and other participants
        this.sendWebSocketMessage({
            type: 'recording_start'
        });
        
        // Show notification
        this.showNotification('Recording started');
        
        console.log('Recording started with MIME type:', mimeType || 'default');
    } catch (error) {
        console.error('Error starting recording:', error);
        this.showError('Failed to start recording: ' + error.message);
    }
};

/**
 * Stop recording the session
 * Requirements: 6.1, 6.2, 6.3
 */
VideoCallInterface.prototype.stopRecording = async function() {
    if (!this.isRecording || !this.mediaRecorder) {
        return;
    }
    
    try {
        // Stop the MediaRecorder
        if (this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
        
        this.isRecording = false;
        
        // Update UI
        this.updateRecordingButton();
        this.showRecordingIndicator(false);
        
        // Notify server and other participants
        this.sendWebSocketMessage({
            type: 'recording_stop'
        });
        
        // Show notification
        this.showNotification('Recording stopped');
        
        console.log('Recording stopped');
    } catch (error) {
        console.error('Error stopping recording:', error);
        this.showError('Failed to stop recording');
    }
};

/**
 * Send recording chunk to server via WebSocket
 * Requirements: 6.1, 6.2
 */
VideoCallInterface.prototype.sendRecordingChunk = async function(chunk) {
    try {
        // Convert Blob to Base64 for WebSocket transmission
        const reader = new FileReader();
        
        reader.onloadend = () => {
            const base64data = reader.result.split(',')[1]; // Remove data URL prefix
            
            this.sendWebSocketMessage({
                type: 'recording_chunk',
                chunk_data: base64data,
                chunk_size: chunk.size,
                chunk_index: this.recordedChunks.length - 1,
                timestamp: new Date().toISOString()
            });
        };
        
        reader.onerror = (error) => {
            console.error('Error reading recording chunk:', error);
        };
        
        reader.readAsDataURL(chunk);
    } catch (error) {
        console.error('Error sending recording chunk:', error);
    }
};

/**
 * Handle recording started notification from server
 * Requirements: 6.2, 6.3
 */
VideoCallInterface.prototype.handleRecordingStarted = function(message) {
    const userName = message.user_name || 'Someone';
    
    // Show recording indicator to all participants
    this.showGlobalRecordingIndicator(true, userName);
    
    // Show notification
    if (message.user_id !== this.userId) {
        this.showNotification(`${userName} started recording this session`);
    }
    
    console.log('Recording started by:', userName);
};

/**
 * Handle recording stopped notification from server
 * Requirements: 6.2, 6.3
 */
VideoCallInterface.prototype.handleRecordingStopped = function(message) {
    const userName = message.user_name || 'Someone';
    
    // Hide recording indicator
    this.showGlobalRecordingIndicator(false);
    
    // Show notification
    if (message.user_id !== this.userId) {
        this.showNotification(`${userName} stopped recording`);
    }
    
    console.log('Recording stopped by:', userName);
};

/**
 * Update recording button UI
 */
VideoCallInterface.prototype.updateRecordingButton = function() {
    const btn = document.getElementById('toggle-recording');
    if (!btn) return;
    
    const icon = btn.querySelector('i');
    const text = btn.querySelector('.btn-text');
    
    if (this.isRecording) {
        btn.classList.remove('btn-secondary');
        btn.classList.add('btn-danger');
        btn.classList.add('active');
        btn.classList.add('recording-pulse');
        if (icon) icon.className = 'fas fa-stop-circle';
        if (text) text.textContent = 'Stop Recording';
        btn.title = 'Stop recording this session';
    } else {
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-secondary');
        btn.classList.remove('active');
        btn.classList.remove('recording-pulse');
        if (icon) icon.className = 'fas fa-circle';
        if (text) text.textContent = 'Record';
        btn.title = 'Start recording this session';
    }
};

/**
 * Show/hide recording indicator in local video
 * Requirements: 6.2, 6.3
 */
VideoCallInterface.prototype.showRecordingIndicator = function(show) {
    let indicator = document.getElementById('recording-indicator');
    
    if (show && !indicator) {
        // Create recording indicator
        indicator = document.createElement('div');
        indicator.id = 'recording-indicator';
        indicator.className = 'recording-indicator';
        indicator.innerHTML = `
            <i class="fas fa-circle recording-dot"></i>
            <span>REC</span>
        `;
        
        const controlBar = document.querySelector('.video-controls');
        if (controlBar) {
            controlBar.insertBefore(indicator, controlBar.firstChild);
        }
    }
    
    if (indicator) {
        indicator.style.display = show ? 'flex' : 'none';
    }
};

/**
 * Show/hide global recording indicator (when someone else is recording)
 * Requirements: 6.2, 6.3
 */
VideoCallInterface.prototype.showGlobalRecordingIndicator = function(show, userName) {
    let indicator = document.getElementById('global-recording-indicator');
    
    if (show && !indicator) {
        // Create global recording indicator
        indicator = document.createElement('div');
        indicator.id = 'global-recording-indicator';
        indicator.className = 'global-recording-indicator';
        indicator.innerHTML = `
            <i class="fas fa-circle recording-dot"></i>
            <span>This session is being recorded${userName ? ' by ' + userName : ''}</span>
        `;
        
        document.body.appendChild(indicator);
    }
    
    if (indicator) {
        if (show) {
            if (userName) {
                const textSpan = indicator.querySelector('span');
                if (textSpan) {
                    textSpan.textContent = `This session is being recorded by ${userName}`;
                }
            }
            indicator.style.display = 'flex';
        } else {
            indicator.style.display = 'none';
        }
    }
};

/**
 * Download recorded session (for local backup)
 */
VideoCallInterface.prototype.downloadRecording = function() {
    if (this.recordedChunks.length === 0) {
        this.showError('No recording available to download');
        return;
    }
    
    try {
        // Create blob from recorded chunks
        const blob = new Blob(this.recordedChunks, {
            type: 'video/webm'
        });
        
        // Create download link
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `session-${this.sessionId}-${Date.now()}.webm`;
        
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);
        
        this.showNotification('Recording downloaded');
    } catch (error) {
        console.error('Error downloading recording:', error);
        this.showError('Failed to download recording');
    }
};

/**
 * Clean up recording resources
 */
VideoCallInterface.prototype.cleanupRecording = function() {
    if (this.isRecording) {
        this.stopRecording();
    }
    
    if (this.mediaRecorder) {
        this.mediaRecorder = null;
    }
    
    this.recordedChunks = [];
    this.recordingStartTime = null;
};
