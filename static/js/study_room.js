// WebRTC Study Room Implementation
class StudyRoom {
    constructor(config) {
        this.sessionId = config.sessionId;
        this.roomId = config.roomId;
        this.userId = config.userId;
        this.userName = config.userName;
        this.csrfToken = config.csrfToken;
        
        // WebRTC configuration
        this.rtcConfig = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ]
        };
        
        // State management
        this.localStream = null;
        this.screenStream = null;
        this.peers = new Map();
        this.isVideoEnabled = true;
        this.isAudioEnabled = true;
        this.isScreenSharing = false;
        this.isModerator = false;
        
        // WebSocket connection for signaling
        this.socket = null;
        
        // DOM elements
        this.localVideo = document.getElementById('local-video');
        this.videoGrid = document.getElementById('video-grid');
        this.chatMessages = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.participantsList = document.getElementById('participants-list');
        this.participantCount = document.getElementById('participant-count');
        this.screenShareContainer = document.getElementById('screen-share-container');
        this.screenShareVideo = document.getElementById('screen-share-video');
        
        this.init();
    }
    
    async init() {
        try {
            await this.setupLocalMedia();
            this.setupWebSocket();
            this.setupEventListeners();
            this.updateParticipantCount();
        } catch (error) {
            console.error('Failed to initialize study room:', error);
            this.showError('Failed to initialize study room. Please check your camera and microphone permissions.');
        }
    }
    
    async setupLocalMedia() {
        try {
            this.localStream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            this.localVideo.srcObject = this.localStream;
            this.updateMediaControls();
        } catch (error) {
            console.error('Error accessing media devices:', error);
            throw new Error('Could not access camera or microphone');
        }
    }
    
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/study-room/${this.roomId}/`;
        
        this.socket = new WebSocket(wsUrl);
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.joinRoom();
            
            // Hide any reconnection messages
            const reconnectMsg = document.querySelector('.reconnect-message');
            if (reconnectMsg) {
                reconnectMsg.remove();
            }
        };
        
        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleSignalingMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.socket.onclose = (event) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            
            if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
                
                this.showReconnectMessage(`Connection lost. Reconnecting in ${delay/1000} seconds... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                
                setTimeout(() => {
                    if (this.socket.readyState === WebSocket.CLOSED) {
                        this.setupWebSocket();
                    }
                }, delay);
            } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                this.showError('Unable to reconnect to the study room. Please refresh the page.');
            }
        };
        
        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showError('Connection error occurred');
        };
    }
    
    setupEventListeners() {
        // Chat input
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendChatMessage();
            }
        });
        
        // Window beforeunload
        window.addEventListener('beforeunload', () => {
            this.leaveRoom();
        });
        
        // Media device changes
        navigator.mediaDevices.addEventListener('devicechange', () => {
            this.handleDeviceChange();
        });
    }
    
    joinRoom() {
        this.sendSignalingMessage({
            type: 'join',
            userId: this.userId,
            userName: this.userName
        });
    }
    
    async handleSignalingMessage(data) {
        switch (data.type) {
            case 'user-joined':
                await this.handleUserJoined(data);
                break;
            case 'user-left':
                this.handleUserLeft(data);
                break;
            case 'offer':
                await this.handleOffer(data);
                break;
            case 'answer':
                await this.handleAnswer(data);
                break;
            case 'ice-candidate':
                await this.handleIceCandidate(data);
                break;
            case 'chat-message':
                this.handleChatMessage(data);
                break;
            case 'screen-share-start':
                this.handleScreenShareStart(data);
                break;
            case 'screen-share-stop':
                this.handleScreenShareStop(data);
                break;
            case 'moderation-action':
                this.handleModerationAction(data);
                break;
            case 'participants-update':
                this.updateParticipants(data.participants);
                break;
        }
    }
    
    async handleUserJoined(data) {
        const { userId, userName } = data;
        
        if (userId === this.userId) return;
        
        // Create peer connection
        const peerConnection = new RTCPeerConnection(this.rtcConfig);
        this.peers.set(userId, {
            connection: peerConnection,
            userName: userName,
            videoElement: null
        });
        
        // Add local stream to peer connection
        this.localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, this.localStream);
        });
        
        // Handle remote stream
        peerConnection.ontrack = (event) => {
            this.handleRemoteStream(userId, event.streams[0]);
        };
        
        // Handle ICE candidates
        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.sendSignalingMessage({
                    type: 'ice-candidate',
                    candidate: event.candidate,
                    targetUserId: userId
                });
            }
        };
        
        // Handle connection state changes
        peerConnection.onconnectionstatechange = () => {
            console.log(`Connection state with ${userName}: ${peerConnection.connectionState}`);
            
            if (peerConnection.connectionState === 'failed') {
                console.log('Connection failed, attempting to restart ICE');
                peerConnection.restartIce();
            } else if (peerConnection.connectionState === 'disconnected') {
                console.log('Connection disconnected');
                // Could implement reconnection logic here
            }
        };
        
        // Handle ICE connection state changes
        peerConnection.oniceconnectionstatechange = () => {
            console.log(`ICE connection state with ${userName}: ${peerConnection.iceConnectionState}`);
            
            if (peerConnection.iceConnectionState === 'failed') {
                this.showError(`Connection lost with ${userName}`);
            }
        };
        
        // Create and send offer
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        
        this.sendSignalingMessage({
            type: 'offer',
            offer: offer,
            targetUserId: userId
        });
        
        this.addParticipant(userId, userName);
        this.updateVideoGrid();
    }
    
    handleUserLeft(data) {
        const { userId } = data;
        
        if (this.peers.has(userId)) {
            const peer = this.peers.get(userId);
            peer.connection.close();
            
            if (peer.videoElement) {
                peer.videoElement.remove();
            }
            
            this.peers.delete(userId);
            this.removeParticipant(userId);
            this.updateVideoGrid();
        }
    }
    
    async handleOffer(data) {
        const { offer, userId, userName } = data;
        
        // Create peer connection
        const peerConnection = new RTCPeerConnection(this.rtcConfig);
        this.peers.set(userId, {
            connection: peerConnection,
            userName: userName,
            videoElement: null
        });
        
        // Add local stream
        this.localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, this.localStream);
        });
        
        // Handle remote stream
        peerConnection.ontrack = (event) => {
            this.handleRemoteStream(userId, event.streams[0]);
        };
        
        // Handle ICE candidates
        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.sendSignalingMessage({
                    type: 'ice-candidate',
                    candidate: event.candidate,
                    targetUserId: userId
                });
            }
        };
        
        // Handle connection state changes
        peerConnection.onconnectionstatechange = () => {
            console.log(`Connection state with ${userName}: ${peerConnection.connectionState}`);
            
            if (peerConnection.connectionState === 'failed') {
                console.log('Connection failed, attempting to restart ICE');
                peerConnection.restartIce();
            }
        };
        
        // Handle ICE connection state changes
        peerConnection.oniceconnectionstatechange = () => {
            console.log(`ICE connection state with ${userName}: ${peerConnection.iceConnectionState}`);
            
            if (peerConnection.iceConnectionState === 'failed') {
                this.showError(`Connection lost with ${userName}`);
            }
        };
        
        // Set remote description and create answer
        await peerConnection.setRemoteDescription(offer);
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        
        this.sendSignalingMessage({
            type: 'answer',
            answer: answer,
            targetUserId: userId
        });
        
        this.addParticipant(userId, userName);
        this.updateVideoGrid();
    }
    
    async handleAnswer(data) {
        const { answer, userId } = data;
        
        if (this.peers.has(userId)) {
            const peer = this.peers.get(userId);
            await peer.connection.setRemoteDescription(answer);
        }
    }
    
    async handleIceCandidate(data) {
        const { candidate, userId } = data;
        
        if (this.peers.has(userId)) {
            const peer = this.peers.get(userId);
            await peer.connection.addIceCandidate(candidate);
        }
    }
    
    handleRemoteStream(userId, stream) {
        const peer = this.peers.get(userId);
        if (!peer) return;
        
        // Create video element for remote stream
        const videoContainer = document.createElement('div');
        videoContainer.className = 'participant-video';
        videoContainer.id = `participant-${userId}`;
        
        const video = document.createElement('video');
        video.srcObject = stream;
        video.autoplay = true;
        video.playsinline = true;
        
        const participantInfo = document.createElement('div');
        participantInfo.className = 'participant-info';
        participantInfo.textContent = peer.userName;
        
        const participantControls = document.createElement('div');
        participantControls.className = 'participant-controls';
        
        if (this.isModerator) {
            const muteBtn = document.createElement('button');
            muteBtn.className = 'control-btn';
            muteBtn.textContent = '🔇';
            muteBtn.onclick = () => this.muteParticipant(userId);
            
            const kickBtn = document.createElement('button');
            kickBtn.className = 'control-btn';
            kickBtn.textContent = '❌';
            kickBtn.onclick = () => this.kickParticipant(userId);
            
            participantControls.appendChild(muteBtn);
            participantControls.appendChild(kickBtn);
        }
        
        videoContainer.appendChild(video);
        videoContainer.appendChild(participantInfo);
        videoContainer.appendChild(participantControls);
        
        this.videoGrid.appendChild(videoContainer);
        peer.videoElement = videoContainer;
        
        this.updateVideoGrid();
    }
    
    handleChatMessage(data) {
        const { userId, userName, message, timestamp } = data;
        this.addChatMessage(userId, userName, message, timestamp);
    }
    
    handleScreenShareStart(data) {
        const { userId, userName } = data;
        this.screenShareContainer.classList.add('active');
        document.getElementById('screen-share-presenter').textContent = userName;
    }
    
    handleScreenShareStop(data) {
        this.screenShareContainer.classList.remove('active');
        this.screenShareVideo.srcObject = null;
    }
    
    handleModerationAction(data) {
        const { action, targetUserId, reason } = data;
        
        if (targetUserId === this.userId) {
            switch (action) {
                case 'mute':
                    this.isAudioEnabled = false;
                    this.updateMediaControls();
                    this.showNotification(`You have been muted by a moderator. Reason: ${reason}`);
                    break;
                case 'kick':
                    this.showNotification(`You have been removed from the room. Reason: ${reason}`);
                    this.leaveRoom();
                    break;
            }
        }
    }
    
    sendSignalingMessage(message) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
        }
    }
    
    sendChatMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;
        
        // Basic client-side content filtering
        if (this.contentFilter && this.isMessageInappropriate(message)) {
            this.showError('Message contains inappropriate content and was not sent.');
            return;
        }
        
        // Rate limiting - prevent spam
        const now = Date.now();
        if (this.lastMessageTime && (now - this.lastMessageTime) < 1000) {
            this.showError('Please wait before sending another message.');
            return;
        }
        this.lastMessageTime = now;
        
        this.sendSignalingMessage({
            type: 'chat-message',
            message: message,
            userId: this.userId,
            userName: this.userName
        });
        
        this.chatInput.value = '';
    }
    
    isMessageInappropriate(message) {
        // Basic client-side content filtering
        const inappropriateWords = [
            'spam', 'scam', 'hack', 'cheat', 'inappropriate'
            // Add more words as needed
        ];
        
        const messageLower = message.toLowerCase();
        return inappropriateWords.some(word => messageLower.includes(word));
    }
    
    addChatMessage(userId, userName, message, timestamp) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${userId === this.userId ? 'own' : 'other'}`;
        
        const senderDiv = document.createElement('div');
        senderDiv.className = 'message-sender';
        senderDiv.textContent = userId === this.userId ? 'You' : userName;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = message;
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date(timestamp).toLocaleTimeString();
        
        messageDiv.appendChild(senderDiv);
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);
        
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    addParticipant(userId, userName) {
        const participantDiv = document.createElement('div');
        participantDiv.className = 'participant-item';
        participantDiv.id = `participant-list-${userId}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'participant-avatar';
        avatar.textContent = userName.charAt(0).toUpperCase();
        
        const details = document.createElement('div');
        details.className = 'participant-details';
        
        const name = document.createElement('div');
        name.className = 'participant-name';
        name.textContent = userName;
        
        const status = document.createElement('div');
        status.className = 'participant-status';
        status.innerHTML = '<div class="status-indicator online"></div>Online';
        
        details.appendChild(name);
        details.appendChild(status);
        
        participantDiv.appendChild(avatar);
        participantDiv.appendChild(details);
        
        if (this.isModerator && userId !== this.userId) {
            const controls = document.createElement('div');
            controls.className = 'moderator-controls';
            
            const muteBtn = document.createElement('button');
            muteBtn.className = 'mod-btn';
            muteBtn.textContent = 'Mute';
            muteBtn.onclick = () => this.muteParticipant(userId);
            
            const kickBtn = document.createElement('button');
            kickBtn.className = 'mod-btn danger';
            kickBtn.textContent = 'Kick';
            kickBtn.onclick = () => this.kickParticipant(userId);
            
            controls.appendChild(muteBtn);
            controls.appendChild(kickBtn);
            participantDiv.appendChild(controls);
        }
        
        this.participantsList.appendChild(participantDiv);
        this.updateParticipantCount();
    }
    
    removeParticipant(userId) {
        const participantElement = document.getElementById(`participant-list-${userId}`);
        if (participantElement) {
            participantElement.remove();
        }
        this.updateParticipantCount();
    }
    
    updateParticipants(participants) {
        // Clear current participants list (except self)
        const currentParticipants = this.participantsList.querySelectorAll('.participant-item');
        currentParticipants.forEach(p => {
            if (!p.id.includes(this.userId)) {
                p.remove();
            }
        });
        
        // Add all participants
        participants.forEach(participant => {
            if (participant.userId !== this.userId) {
                this.addParticipant(participant.userId, participant.userName);
            }
        });
    }
    
    updateParticipantCount() {
        const count = this.participantsList.children.length;
        this.participantCount.textContent = count;
        document.getElementById('participants-count').textContent = count;
    }
    
    updateVideoGrid() {
        const participantCount = this.peers.size + 1; // +1 for local video
        this.videoGrid.className = `video-grid participants-${Math.min(participantCount, 6)}`;
    }
    
    async toggleCamera() {
        if (this.localStream) {
            const videoTrack = this.localStream.getVideoTracks()[0];
            if (videoTrack) {
                videoTrack.enabled = !videoTrack.enabled;
                this.isVideoEnabled = videoTrack.enabled;
                this.updateMediaControls();
            }
        }
    }
    
    async toggleMicrophone() {
        if (this.localStream) {
            const audioTrack = this.localStream.getAudioTracks()[0];
            if (audioTrack) {
                audioTrack.enabled = !audioTrack.enabled;
                this.isAudioEnabled = audioTrack.enabled;
                this.updateMediaControls();
            }
        }
    }
    
    async toggleScreenShare() {
        if (this.isScreenSharing) {
            await this.stopScreenShare();
        } else {
            await this.startScreenShare();
        }
    }
    
    async startScreenShare() {
        try {
            // Check if screen sharing is supported
            if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
                this.showError('Screen sharing is not supported in this browser');
                return;
            }
            
            this.screenStream = await navigator.mediaDevices.getDisplayMedia({
                video: {
                    cursor: 'always',
                    displaySurface: 'monitor'
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 44100
                }
            });
            
            // Replace video track in all peer connections
            const videoTrack = this.screenStream.getVideoTracks()[0];
            
            // Update all peer connections with screen share
            const replacePromises = [];
            this.peers.forEach((peer) => {
                const sender = peer.connection.getSenders().find(s => 
                    s.track && s.track.kind === 'video'
                );
                if (sender) {
                    replacePromises.push(sender.replaceTrack(videoTrack));
                }
            });
            
            await Promise.all(replacePromises);
            
            // Update local video
            this.localVideo.srcObject = this.screenStream;
            this.isScreenSharing = true;
            
            // Handle screen share end (user clicks stop sharing in browser)
            videoTrack.onended = () => {
                this.stopScreenShare();
            };
            
            // Show screen share in dedicated area
            this.screenShareVideo.srcObject = this.screenStream;
            this.screenShareContainer.classList.add('active');
            
            this.sendSignalingMessage({
                type: 'screen-share-start',
                userId: this.userId,
                userName: this.userName
            });
            
            this.updateScreenShareControls();
            this.showNotification('Screen sharing started');
            
        } catch (error) {
            console.error('Error starting screen share:', error);
            if (error.name === 'NotAllowedError') {
                this.showError('Screen sharing permission denied');
            } else if (error.name === 'NotSupportedError') {
                this.showError('Screen sharing is not supported');
            } else {
                this.showError('Could not start screen sharing: ' + error.message);
            }
        }
    }
    
    async stopScreenShare() {
        if (this.screenStream) {
            this.screenStream.getTracks().forEach(track => track.stop());
            this.screenStream = null;
        }
        
        // Replace with camera stream
        const videoTrack = this.localStream.getVideoTracks()[0];
        
        // Update all peer connections back to camera
        const replacePromises = [];
        this.peers.forEach((peer) => {
            const sender = peer.connection.getSenders().find(s => 
                s.track && s.track.kind === 'video'
            );
            if (sender && videoTrack) {
                replacePromises.push(sender.replaceTrack(videoTrack));
            }
        });
        
        try {
            await Promise.all(replacePromises);
        } catch (error) {
            console.error('Error stopping screen share:', error);
        }
        
        this.localVideo.srcObject = this.localStream;
        this.isScreenSharing = false;
        
        // Hide screen share area
        this.screenShareContainer.classList.remove('active');
        this.screenShareVideo.srcObject = null;
        
        this.sendSignalingMessage({
            type: 'screen-share-stop',
            userId: this.userId
        });
        
        this.updateScreenShareControls();
        this.showNotification('Screen sharing stopped');
    }
    
    updateMediaControls() {
        const micBtn = document.getElementById('mic-btn');
        const cameraBtn = document.getElementById('camera-btn');
        
        micBtn.className = `toolbar-btn ${this.isAudioEnabled ? 'active' : 'inactive'}`;
        cameraBtn.className = `toolbar-btn ${this.isVideoEnabled ? 'active' : 'inactive'}`;
        
        // Update video toggle button
        const videoToggle = document.getElementById('video-toggle');
        if (videoToggle) {
            videoToggle.textContent = this.isVideoEnabled ? '📹' : '📹❌';
        }
        
        // Update audio toggle button
        const audioToggle = document.getElementById('audio-toggle');
        if (audioToggle) {
            audioToggle.textContent = this.isAudioEnabled ? '🎤' : '🎤❌';
        }
    }
    
    updateScreenShareControls() {
        const screenBtn = document.getElementById('screen-btn');
        screenBtn.className = `toolbar-btn ${this.isScreenSharing ? 'active' : 'inactive'}`;
        screenBtn.innerHTML = this.isScreenSharing ? 
            '<span>🖥️</span><span>Stop Sharing</span>' : 
            '<span>🖥️</span><span>Share Screen</span>';
    }
    
    muteParticipant(userId) {
        const reason = prompt('Reason for muting (optional):') || 'Muted by moderator';
        this.sendSignalingMessage({
            type: 'moderation-action',
            action: 'mute',
            targetUserId: userId,
            reason: reason
        });
        this.showNotification('Participant has been muted');
    }
    
    kickParticipant(userId) {
        const reason = prompt('Reason for removal:');
        if (reason && confirm('Are you sure you want to remove this participant?')) {
            this.sendSignalingMessage({
                type: 'moderation-action',
                action: 'kick',
                targetUserId: userId,
                reason: reason
            });
            this.showNotification('Participant has been removed from the room');
        }
    }
    
    enableSafetyMode() {
        // Enable additional safety features
        this.safetyMode = true;
        
        // Add content filtering for chat
        this.contentFilter = true;
        
        // Enable automatic moderation
        this.autoModeration = true;
        
        this.showNotification('Safety mode enabled');
    }
    
    reportParticipant(userId, userName) {
        // Show report modal with pre-filled participant info
        document.getElementById('moderation-modal').classList.remove('hidden');
        document.getElementById('issue-description').placeholder = 
            `Report issue with ${userName}. Please describe the inappropriate behavior...`;
    }
    
    reportIssue() {
        document.getElementById('moderation-modal').classList.remove('hidden');
    }
    
    closeModerationModal() {
        document.getElementById('moderation-modal').classList.add('hidden');
    }
    
    submitReport() {
        const issueType = document.getElementById('issue-type').value;
        const description = document.getElementById('issue-description').value;
        
        if (!description.trim()) {
            alert('Please provide a description of the issue.');
            return;
        }
        
        // Send report to server
        fetch('/api/study-room/report/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify({
                sessionId: this.sessionId,
                issueType: issueType,
                description: description
            })
        }).then(response => {
            if (response.ok) {
                this.showNotification('Report submitted successfully. Thank you for helping keep our community safe.');
                this.closeModerationModal();
            } else {
                this.showError('Failed to submit report. Please try again.');
            }
        }).catch(error => {
            console.error('Error submitting report:', error);
            this.showError('Failed to submit report. Please try again.');
        });
    }
    
    async handleDeviceChange() {
        // Refresh media devices if needed
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            console.log('Available devices:', devices);
        } catch (error) {
            console.error('Error enumerating devices:', error);
        }
    }
    
    leaveRoom() {
        // Close all peer connections
        this.peers.forEach(peer => {
            peer.connection.close();
        });
        this.peers.clear();
        
        // Stop local streams
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
        }
        
        if (this.screenStream) {
            this.screenStream.getTracks().forEach(track => track.stop());
        }
        
        // Close WebSocket
        if (this.socket) {
            this.socket.close();
        }
        
        // Redirect to session detail page
        window.location.href = `/community/study-sessions/${this.sessionId}/`;
    }
    
    showError(message) {
        // Create error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50';
        errorDiv.innerHTML = `
            <strong class="font-bold">Error:</strong>
            <span class="block sm:inline">${message}</span>
            <button onclick="this.parentElement.remove()" class="float-right ml-4 text-red-500 hover:text-red-700">×</button>
        `;
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }
    
    showNotification(message) {
        // Create success notification
        const notificationDiv = document.createElement('div');
        notificationDiv.className = 'fixed top-4 right-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded z-50';
        notificationDiv.innerHTML = `
            <span class="block sm:inline">${message}</span>
            <button onclick="this.parentElement.remove()" class="float-right ml-4 text-green-500 hover:text-green-700">×</button>
        `;
        document.body.appendChild(notificationDiv);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notificationDiv.parentElement) {
                notificationDiv.remove();
            }
        }, 3000);
    }
    
    showReconnectMessage(message) {
        // Remove existing reconnect message
        const existingMsg = document.querySelector('.reconnect-message');
        if (existingMsg) {
            existingMsg.remove();
        }
        
        // Create reconnect notification
        const reconnectDiv = document.createElement('div');
        reconnectDiv.className = 'reconnect-message fixed top-4 left-1/2 transform -translate-x-1/2 bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded z-50';
        reconnectDiv.innerHTML = `
            <div class="flex items-center">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-700 mr-2"></div>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(reconnectDiv);
    }
    
    showConnectionStatus(status) {
        const statusIndicator = document.getElementById('connection-status');
        if (statusIndicator) {
            statusIndicator.className = `connection-status ${status}`;
            statusIndicator.textContent = status === 'connected' ? 'Connected' : 
                                        status === 'connecting' ? 'Connecting...' : 'Disconnected';
        }
    }
}

// Global functions for template compatibility
let studyRoom = null;

function initializeStudyRoom(config) {
    studyRoom = new StudyRoom(config);
}

function toggleMicrophone() {
    if (studyRoom) studyRoom.toggleMicrophone();
}

function toggleCamera() {
    if (studyRoom) studyRoom.toggleCamera();
}

function toggleScreenShare() {
    if (studyRoom) studyRoom.toggleScreenShare();
}

function toggleVideo() {
    if (studyRoom) studyRoom.toggleCamera();
}

function toggleAudio() {
    if (studyRoom) studyRoom.toggleMicrophone();
}

function sendMessage() {
    if (studyRoom) studyRoom.sendChatMessage();
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function leaveRoom() {
    if (studyRoom) studyRoom.leaveRoom();
}

function reportIssue() {
    if (studyRoom) studyRoom.reportIssue();
}

function closeModerationModal() {
    if (studyRoom) studyRoom.closeModerationModal();
}

function submitReport() {
    if (studyRoom) studyRoom.submitReport();
}

function toggleWhiteboard() {
    // Basic whiteboard implementation
    if (studyRoom) {
        studyRoom.toggleWhiteboard();
    }
}

// Add whiteboard functionality to StudyRoom class
StudyRoom.prototype.toggleWhiteboard = function() {
    const whiteboardContainer = document.getElementById('whiteboard-container');
    
    if (!whiteboardContainer) {
        // Create whiteboard container
        const container = document.createElement('div');
        container.id = 'whiteboard-container';
        container.className = 'fixed inset-0 bg-black bg-opacity-75 z-50 hidden';
        container.innerHTML = `
            <div class="flex items-center justify-center min-h-screen p-4">
                <div class="bg-white rounded-lg w-full max-w-4xl h-96 relative">
                    <div class="flex justify-between items-center p-4 border-b">
                        <h3 class="text-lg font-semibold">Collaborative Whiteboard</h3>
                        <button onclick="toggleWhiteboard()" class="text-gray-500 hover:text-gray-700">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                    <canvas id="whiteboard-canvas" class="w-full h-80 cursor-crosshair"></canvas>
                    <div class="flex justify-center space-x-4 p-4 border-t">
                        <button class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">Pen</button>
                        <button class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600">Eraser</button>
                        <button class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">Clear</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(container);
        
        // Initialize canvas drawing
        this.initializeWhiteboard();
    }
    
    const whiteboard = document.getElementById('whiteboard-container');
    whiteboard.classList.toggle('hidden');
};

StudyRoom.prototype.initializeWhiteboard = function() {
    const canvas = document.getElementById('whiteboard-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    let isDrawing = false;
    
    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    
    // Drawing functions
    canvas.addEventListener('mousedown', (e) => {
        isDrawing = true;
        ctx.beginPath();
        ctx.moveTo(e.offsetX, e.offsetY);
    });
    
    canvas.addEventListener('mousemove', (e) => {
        if (!isDrawing) return;
        ctx.lineTo(e.offsetX, e.offsetY);
        ctx.stroke();
    });
    
    canvas.addEventListener('mouseup', () => {
        isDrawing = false;
    });
    
    // Set default drawing style
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
};