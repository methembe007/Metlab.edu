# Video Chat Scalability Fix Implementation Plan

## Overview
This document outlines the implementation plan to fix the three critical issues identified in the architecture analysis.

## Issue 1: SFU Implementation for Large Groups

### Current Problem
- P2P mesh topology requires each participant to maintain N-1 connections
- For 30 participants: 29 connections per user = ~29 Mbps upload bandwidth
- CPU overhead: encoding/decoding 29 video streams simultaneously

### Solution: Hybrid Architecture
Implement a hybrid approach that uses P2P for small sessions and SFU for large sessions.

**Decision Logic:**
- 1-6 participants: Use P2P mesh (current implementation)
- 7+ participants: Use SFU (Mediasoup-based)

### Implementation Steps

#### Step 1: Install Mediasoup (SFU Server)
```bash
npm install mediasoup mediasoup-client
```

#### Step 2: Create SFU Service
Location: `video_chat/sfu_service.py`

#### Step 3: Update Frontend to Support Both Modes
Location: `static/js/video_call_sfu.js`

#### Step 4: Add Configuration
Location: `metlab_edu/settings.py`

---

## Issue 2: TURN Server Configuration

### Current Problem
- Only STUN servers configured
- ~10-15% of users behind symmetric NATs cannot connect

### Solution: Coturn TURN Server

#### Option A: Self-Hosted Coturn (Recommended for Production)

**Installation (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install coturn
```

**Configuration:** `/etc/turnserver.conf`

#### Option B: Cloud TURN Service (Quick Start)

Use Twilio's TURN service or Metered.ca for immediate deployment.

---

## Issue 3: Enhanced Recording System

### Current Problem
- Client-side recording only
- WebSocket chunk transfer inefficient
- No multi-participant mixing

### Solution: Server-Side Recording with Janus

#### Implementation Approach
1. Use Janus Gateway's recording plugin
2. Record all participant streams server-side
3. Mix streams using FFmpeg
4. Store in cloud storage (S3/GCS)

---

## Implementation Priority

### Phase 1: TURN Server (1-2 days) - IMMEDIATE
- Quick win, solves connectivity issues
- Can use cloud service initially

### Phase 2: SFU Implementation (2-3 weeks) - HIGH PRIORITY
- Critical for scalability
- Requires significant development

### Phase 3: Recording Enhancement (2 weeks) - MEDIUM PRIORITY
- Current system works, but inefficient
- Can be improved post-launch

---

## Estimated Timeline

- **Week 1**: TURN server setup + testing
- **Week 2-4**: SFU implementation + integration
- **Week 5-6**: Recording enhancement
- **Week 7**: Load testing + optimization
- **Week 8**: Production deployment

**Total: 8 weeks to full implementation**

---

## Quick Wins (Can Deploy Immediately)

### 1. Limit Group Sessions to 6 Participants
Add validation in `VideoSessionService.create_session()`:

```python
if session_type in ['group', 'class'] and max_participants > 6:
    raise ValidationError(
        "Group sessions are currently limited to 6 participants. "
        "For larger groups, please contact support."
    )
```

### 2. Add TURN Server via Cloud Service
Use Twilio or Metered.ca immediately while setting up Coturn.

### 3. Disable Recording for Large Groups
Add check in recording handler:

```python
if session.participants.count() > 6:
    raise ValidationError("Recording is only available for sessions with 6 or fewer participants")
```

---

## Next Steps

1. Review and approve this plan
2. Set up TURN server (cloud service for immediate use)
3. Begin SFU implementation
4. Schedule load testing sessions
5. Plan production rollout

