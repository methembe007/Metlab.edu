# Video Chat System - Implementation Roadmap

## Overview

This roadmap provides a prioritized, actionable plan to address the findings from the architecture analysis and prepare the video chat system for production deployment.

---

## Phase 1: Critical Fixes (Week 1-2)

### 1.1 TURN Server Setup (Priority: CRITICAL)

**Objective:** Enable connectivity for users behind restrictive NATs/firewalls

**Tasks:**
- [ ] Choose TURN solution (Coturn recommended for self-hosted)
- [ ] Deploy TURN server on separate instance
- [ ] Configure credentials and security
- [ ] Update Django settings with TURN configuration
- [ ] Test connectivity from restrictive networks

**Deliverables:**
- Working TURN server
- Updated `settings.py` with TURN credentials
- Connection success rate > 95%

**Estimated Time:** 2-3 days

**See:** `TURN_SERVER_SETUP_GUIDE.md` for detailed instructions

---

### 1.2 Load Testing Framework (Priority: CRITICAL)

**Objective:** Validate system performance under realistic load

**Tasks:**
- [ ] Create load testing script for 2-6 participants
- [ ] Create load testing script for 10-30 participants
- [ ] Measure CPU, memory, bandwidth usage
- [ ] Document performance baselines
- [ ] Identify bottlenecks

**Test Scenarios:**
```python
# test_video_chat_load.py
1. 2 participants (1-on-1) - 10 concurrent sessions
2. 6 participants (small group) - 5 concurrent sessions
3. 15 participants (medium group) - 2 concurrent sessions
4. 30 participants (large group) - 1 session
```

**Success Criteria:**
- 1-on-1: < 100ms latency, < 2% packet loss
- Small group (6): < 150ms latency, < 3% packet loss
- Large group (30): Document actual performance

**Estimated Time:** 3-4 days

---

### 1.3 Mobile Browser Testing (Priority: HIGH)

**Objective:** Ensure compatibility with iOS Safari and Chrome Mobile

**Tasks:**
- [ ] Test on iOS Safari (iPhone 12+, iPad)
- [ ] Test on Chrome Mobile (Android 10+)
- [ ] Fix mobile-specific WebRTC issues
- [ ] Optimize UI for mobile screens
- [ ] Test camera/microphone permissions flow

**Known Mobile Issues to Check:**
```javascript
// iOS Safari specific
- Autoplay restrictions
- getUserMedia() in non-secure contexts
- Video element sizing issues
- Background tab behavior

// Chrome Mobile specific
- Battery optimization interference
- Data saver mode impact
- Screen rotation handling
```

**Estimated Time:** 3-4 days

---

## Phase 2: Scalability Enhancement (Week 3-5)

### 2.1 SFU Integration (Priority: HIGH)

**Objective:** Enable scalable group sessions with 10-30 participants

**Recommended Solution: Janus Gateway**

**Why Janus:**
- Open source, battle-tested
- Excellent performance (C-based)
- Good documentation
- Active community
- Supports recording

**Implementation Steps:**

#### Step 1: Install Janus (Day 1-2)
```bash
# Install dependencies
sudo apt-get install libmicrohttpd-dev libjansson-dev \
    libssl-dev libsrtp2-dev libsofia-sip-ua-dev \
    libglib2.0-dev libopus-dev libogg-dev libcurl4-openssl-dev \
    liblua5.3-dev libconfig-dev pkg-config gengetopt \
    libtool automake

# Clone and build Janus
git clone https://github.com/meetecho/janus-gateway.git
cd janus-gateway
sh autogen.sh
./configure --prefix=/opt/janus
make
sudo make install
```

#### Step 2: Configure Janus (Day 2-3)
```ini
# /opt/janus/etc/janus/janus.jcfg
general: {
    admin_secret = "your-admin-secret"
    api_secret = "your-api-secret"
}

nat: {
    stun_server = "stun.l.google.com"
    stun_port = 19302
    turn_server = "your-turn-server.com"
    turn_port = 3478
    turn_type = "udp"
    turn_user = "username"
    turn_pwd = "password"
}

# Enable VideoRoom plugin
plugins: {
    videoroom: {
        enabled = true
    }
}
```

#### Step 3: Create Django Integration (Day 3-5)
```python
# video_chat/sfu_adapter.py
import requests
import json
from django.conf import settings

class JanusAdapter:
    """Adapter for Janus SFU integration"""
    
    def __init__(self):
        self.janus_url = settings.JANUS_SERVER_URL
        self.api_secret = settings.JANUS_API_SECRET
        self.session_id = None
        self.handle_id = None
    
    def create_room(self, room_id, max_publishers=30):
        """Create a Janus VideoRoom"""
        payload = {
            "janus": "create",
            "transaction": f"create_{room_id}",
            "plugin": "janus.plugin.videoroom",
            "request": {
                "room": room_id,
                "description": f"Video Session {room_id}",
                "publishers": max_publishers,
                "bitrate": 1024000,  # 1 Mbps
                "fir_freq": 10,
                "audiocodec": "opus",
                "videocodec": "vp8"
            }
        }
        
        response = requests.post(
            f"{self.janus_url}/janus",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        return response.json()
    
    def destroy_room(self, room_id):
        """Destroy a Janus VideoRoom"""
        payload = {
            "janus": "destroy",
            "transaction": f"destroy_{room_id}",
            "plugin": "janus.plugin.videoroom",
            "request": {
                "room": room_id
            }
        }
        
        response = requests.post(
            f"{self.janus_url}/janus",
            json=payload
        )
        
        return response.json()
```

#### Step 4: Update Frontend (Day 6-8)
```javascript
// static/js/video_call_sfu.js
class VideoCallSFU extends VideoCallInterface {
    constructor(sessionId, userId, userName, useSFU = false) {
        super(sessionId, userId, userName);
        this.useSFU = useSFU;
        this.janusSession = null;
        this.videoRoomHandle = null;
    }
    
    async initializeJanus() {
        // Initialize Janus session
        this.janusSession = new Janus({
            server: JANUS_SERVER_URL,
            success: () => {
                console.log('Janus session created');
                this.attachVideoRoomPlugin();
            },
            error: (error) => {
                console.error('Janus error:', error);
                this.showError('Failed to connect to video server');
            }
        });
    }
    
    attachVideoRoomPlugin() {
        this.janusSession.attach({
            plugin: "janus.plugin.videoroom",
            success: (pluginHandle) => {
                this.videoRoomHandle = pluginHandle;
                this.joinRoom();
            },
            error: (error) => {
                console.error('Plugin attach error:', error);
            },
            onmessage: (msg, jsep) => {
                this.handleJanusMessage(msg, jsep);
            },
            onlocalstream: (stream) => {
                this.displayLocalVideo(stream);
            },
            onremotestream: (stream) => {
                this.displayRemoteVideo(stream);
            }
        });
    }
    
    joinRoom() {
        const register = {
            request: "join",
            room: this.sessionId,
            ptype: "publisher",
            display: this.userName
        };
        
        this.videoRoomHandle.send({ message: register });
    }
}
```

#### Step 5: Hybrid Mode Implementation (Day 9-10)
```python
# video_chat/services.py
def create_session(host, session_type, **kwargs):
    # Determine if SFU should be used
    use_sfu = False
    
    if session_type in ['group', 'class']:
        max_participants = kwargs.get('max_participants', 30)
        if max_participants > 6:
            use_sfu = True
    
    session = VideoSession.objects.create(
        session_type=session_type,
        host=host,
        use_sfu=use_sfu,  # New field
        **kwargs
    )
    
    # Create Janus room if using SFU
    if use_sfu:
        from .sfu_adapter import JanusAdapter
        janus = JanusAdapter()
        janus.create_room(str(session.session_id), max_participants)
    
    return session
```

**Success Criteria:**
- 30 participants with < 200ms latency
- CPU usage < 50% per client
- Bandwidth < 5 Mbps per client

**Estimated Time:** 10-12 days

---

### 2.2 Database Migration for SFU Support

**Add new fields to VideoSession model:**

```python
# video_chat/migrations/0002_add_sfu_support.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('video_chat', '0001_initial'),
    ]
    
    operations = [
        migrations.AddField(
            model_name='videosession',
            name='use_sfu',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='videosession',
            name='sfu_room_id',
            field=models.CharField(max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='videosession',
            name='sfu_server_url',
            field=models.URLField(blank=True),
        ),
    ]
```

**Estimated Time:** 1 day

---

## Phase 3: Recording Enhancement (Week 6-7)

### 3.1 Server-Side Recording with Janus

**Objective:** Implement reliable multi-participant recording

**Implementation:**

```python
# video_chat/recording_service.py
import subprocess
import os
from django.conf import settings

class JanusRecordingService:
    """Service for managing Janus recordings"""
    
    def start_recording(self, session_id):
        """Start recording a Janus room"""
        # Enable recording in Janus VideoRoom
        payload = {
            "request": "enable_recording",
            "room": session_id,
            "record": True
        }
        
        # Send to Janus via admin API
        # Janus will record all participants' streams
        
    def stop_recording(self, session_id):
        """Stop recording and process files"""
        # Disable recording
        # Janus saves .mjr files for each stream
        
    def process_recording(self, session_id):
        """Convert and merge Janus recordings"""
        recording_dir = f"/opt/janus/recordings/{session_id}"
        
        # Convert .mjr files to .webm
        for mjr_file in os.listdir(recording_dir):
            if mjr_file.endswith('.mjr'):
                webm_file = mjr_file.replace('.mjr', '.webm')
                subprocess.run([
                    '/opt/janus/bin/janus-pp-rec',
                    f'{recording_dir}/{mjr_file}',
                    f'{recording_dir}/{webm_file}'
                ])
        
        # Merge all streams using FFmpeg
        self.merge_streams(recording_dir, session_id)
    
    def merge_streams(self, recording_dir, session_id):
        """Merge multiple video streams into single file"""
        # Use FFmpeg to create grid layout
        # This is complex - consider using cloud service
        pass
```

**Alternative: Cloud Recording Service**

Consider using:
- **Agora Cloud Recording** (easiest, paid)
- **Twilio Recordings** (reliable, paid)
- **Daily.co Recordings** (good quality, paid)

**Estimated Time:** 5-7 days (self-hosted) or 2-3 days (cloud service)

---

## Phase 4: Monitoring & Observability (Week 8)

### 4.1 Metrics Collection

**Implement Prometheus metrics:**

```python
# video_chat/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Session metrics
video_sessions_total = Counter(
    'video_sessions_total',
    'Total number of video sessions',
    ['session_type', 'status']
)

video_session_duration = Histogram(
    'video_session_duration_seconds',
    'Video session duration in seconds',
    ['session_type']
)

active_participants = Gauge(
    'video_active_participants',
    'Number of active participants',
    ['session_id']
)

# Connection metrics
webrtc_connections_total = Counter(
    'webrtc_connections_total',
    'Total WebRTC connections',
    ['status']
)

connection_quality_score = Histogram(
    'connection_quality_score',
    'Connection quality score (0-100)',
    ['session_id', 'user_id']
)

# Error metrics
video_errors_total = Counter(
    'video_errors_total',
    'Total video chat errors',
    ['error_type']
)
```

**Update services to record metrics:**

```python
# video_chat/services.py
from .metrics import video_sessions_total, video_session_duration

def create_session(host, session_type, **kwargs):
    session = VideoSession.objects.create(...)
    
    # Record metric
    video_sessions_total.labels(
        session_type=session_type,
        status='created'
    ).inc()
    
    return session

def end_session(session_id, user):
    session = VideoSession.objects.get(session_id=session_id)
    duration = (session.ended_at - session.started_at).total_seconds()
    
    # Record metric
    video_session_duration.labels(
        session_type=session.session_type
    ).observe(duration)
    
    video_sessions_total.labels(
        session_type=session.session_type,
        status='completed'
    ).inc()
```

**Estimated Time:** 3-4 days

---

### 4.2 Grafana Dashboards

**Create monitoring dashboards:**

1. **Session Overview Dashboard**
   - Active sessions count
   - Total participants
   - Session duration distribution
   - Session creation rate

2. **Connection Quality Dashboard**
   - Average quality score by session
   - Packet loss distribution
   - RTT distribution
   - Bandwidth usage

3. **Error Dashboard**
   - Error rate by type
   - Failed connection attempts
   - WebSocket disconnections
   - Recording failures

**Estimated Time:** 2-3 days

---

## Phase 5: Testing & Validation (Week 9-10)

### 5.1 Comprehensive Test Suite

**Unit Tests:**
```python
# video_chat/tests/test_services.py
def test_create_session_with_sfu():
    """Test session creation with SFU enabled"""
    session = VideoSessionService.create_session(
        host=teacher_user,
        session_type='class',
        max_participants=30
    )
    assert session.use_sfu == True

def test_join_session_capacity():
    """Test participant limit enforcement"""
    # Create session with max 5 participants
    # Try to add 6th participant
    # Should raise ValidationError
```

**Integration Tests:**
```python
# video_chat/tests/test_integration.py
def test_full_session_lifecycle():
    """Test complete session flow"""
    # Create session
    # Join as multiple participants
    # Exchange media
    # Leave session
    # Verify cleanup
```

**Load Tests:**
```python
# video_chat/tests/test_load.py
def test_30_participant_session():
    """Test 30 concurrent participants"""
    # Simulate 30 WebSocket connections
    # Measure latency, packet loss
    # Verify all participants receive streams
```

**Estimated Time:** 7-10 days

---

### 5.2 Security Audit

**Tasks:**
- [ ] Penetration testing
- [ ] Rate limiting validation
- [ ] Permission bypass attempts
- [ ] WebSocket injection tests
- [ ] TURN credential security review

**Estimated Time:** 3-5 days

---

## Phase 6: Documentation & Deployment (Week 11-12)

### 6.1 Documentation

**Create comprehensive docs:**

1. **Deployment Guide**
   - Infrastructure requirements
   - Server setup instructions
   - Configuration examples
   - Scaling guidelines

2. **Operations Manual**
   - Monitoring setup
   - Troubleshooting guide
   - Backup procedures
   - Disaster recovery

3. **API Documentation**
   - REST API endpoints
   - WebSocket message formats
   - Error codes
   - Rate limits

**Estimated Time:** 5-7 days

---

### 6.2 Staging Deployment

**Deploy to staging environment:**

```bash
# Infrastructure setup
- Web server: 2x 4 CPU, 8GB RAM
- Janus SFU: 2x 8 CPU, 16GB RAM (for 30 participants)
- TURN server: 1x 4 CPU, 8GB RAM
- Redis: 1x 2 CPU, 4GB RAM
- Database: 1x 4 CPU, 8GB RAM
```

**Configuration:**
```python
# settings_staging.py
JANUS_SERVER_URL = 'https://janus-staging.example.com'
TURN_SERVER_URL = 'turn:turn-staging.example.com:3478'

VIDEO_CHAT_MAX_PARTICIPANTS = 30
VIDEO_CHAT_USE_SFU_THRESHOLD = 6  # Use SFU for 6+ participants
```

**Estimated Time:** 3-5 days

---

### 6.3 Production Deployment

**Pre-deployment checklist:**
- [ ] All tests passing
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Monitoring configured
- [ ] Backup procedures tested
- [ ] Rollback plan documented
- [ ] Team trained on operations

**Deployment steps:**
1. Deploy infrastructure
2. Configure services
3. Run database migrations
4. Deploy application code
5. Verify health checks
6. Enable monitoring
7. Gradual rollout (10% → 50% → 100%)

**Estimated Time:** 3-5 days

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1: Critical Fixes | 2 weeks | TURN server, Load tests, Mobile support |
| Phase 2: Scalability | 3 weeks | SFU integration, 30-participant support |
| Phase 3: Recording | 1 week | Server-side recording |
| Phase 4: Monitoring | 1 week | Metrics, Dashboards, Alerts |
| Phase 5: Testing | 2 weeks | Comprehensive test suite, Security audit |
| Phase 6: Deployment | 2 weeks | Documentation, Staging, Production |
| **Total** | **11-12 weeks** | Production-ready video chat system |

---

## Resource Requirements

### Team
- 1 Backend Developer (Django/Python)
- 1 Frontend Developer (JavaScript/WebRTC)
- 1 DevOps Engineer (Infrastructure/Deployment)
- 1 QA Engineer (Testing)

### Infrastructure (Production)
- Web servers: 2x 4 CPU, 8GB RAM ($80/month each)
- Janus SFU: 2x 8 CPU, 16GB RAM ($160/month each)
- TURN server: 1x 4 CPU, 8GB RAM ($80/month)
- Redis: 1x 2 CPU, 4GB RAM ($40/month)
- Database: 1x 4 CPU, 8GB RAM ($80/month)
- Load balancer: $20/month
- **Total: ~$700/month**

### Alternative: Cloud Services
- Twilio Video: ~$0.004/participant-minute
- Agora: ~$0.0099/participant-minute
- Daily.co: ~$0.002/participant-minute

**Cost comparison for 1000 hours/month:**
- Self-hosted: $700/month
- Cloud (Daily.co): ~$120/month (1000 hours × 60 min × $0.002)
- Cloud (Twilio): ~$240/month

---

## Risk Mitigation

### High-Risk Items

1. **SFU Integration Complexity**
   - **Risk:** Janus integration takes longer than expected
   - **Mitigation:** Start with cloud SFU service (Daily.co) as backup plan
   - **Fallback:** Limit group sessions to 6 participants initially

2. **Load Testing Reveals Performance Issues**
   - **Risk:** System can't handle 30 participants
   - **Mitigation:** Optimize before launch, reduce max participants
   - **Fallback:** Implement waiting room for large sessions

3. **TURN Server Costs**
   - **Risk:** TURN bandwidth costs exceed budget
   - **Mitigation:** Monitor usage, implement bandwidth limits
   - **Fallback:** Use cloud TURN service with usage caps

---

## Success Metrics

### Technical Metrics
- Connection success rate: > 95%
- Average latency: < 200ms
- Packet loss: < 3%
- Session uptime: > 99%
- Error rate: < 1%

### Business Metrics
- User satisfaction: > 4.5/5
- Session completion rate: > 90%
- Support tickets: < 5% of sessions
- Adoption rate: > 70% of teachers

---

## Next Steps

1. **Immediate (This Week):**
   - Set up TURN server
   - Begin load testing framework
   - Start mobile browser testing

2. **Short-term (Next 2 Weeks):**
   - Complete Phase 1 critical fixes
   - Begin SFU evaluation and planning
   - Set up staging environment

3. **Medium-term (Next Month):**
   - Complete SFU integration
   - Implement monitoring
   - Comprehensive testing

4. **Long-term (Next 3 Months):**
   - Production deployment
   - User feedback collection
   - Iterative improvements

---

**Document Version:** 1.0
**Last Updated:** April 27, 2026
**Owner:** Development Team
**Review Date:** Weekly during implementation
