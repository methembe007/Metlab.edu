# TURN Server Setup Guide

This guide provides instructions for setting up TURN servers for the MetLab Education video chat system.

## Overview

TURN (Traversal Using Relays around NAT) servers are essential for WebRTC connections when direct peer-to-peer connections fail due to firewalls or NAT restrictions. While STUN servers help discover public IP addresses, TURN servers relay media traffic when direct connections aren't possible.

## Development Setup

For development, the system uses public STUN servers which are sufficient for most testing scenarios:

- `stun:stun.l.google.com:19302`
- `stun:stun1.l.google.com:19302`
- `stun:stun2.l.google.com:19302`
- `stun:stun3.l.google.com:19302`
- `stun:stun4.l.google.com:19302`

These are configured by default in `metlab_edu/settings.py`.

## Production Setup Options

For production, you need a TURN server to ensure reliable connections. You have three main options:

### Option 1: Self-Hosted Coturn Server (Recommended for Full Control)

Coturn is an open-source TURN/STUN server implementation.

#### Installation on Ubuntu/Debian

```bash
# Install Coturn
sudo apt-get update
sudo apt-get install coturn

# Enable Coturn service
sudo systemctl enable coturn
```

#### Configuration

Edit `/etc/turnserver.conf`:

```conf
# Listening port for TURN
listening-port=3478

# TLS listening port (recommended for production)
tls-listening-port=5349

# External IP address
external-ip=YOUR_SERVER_PUBLIC_IP

# Relay IP address (usually same as external IP)
relay-ip=YOUR_SERVER_PUBLIC_IP

# Realm for authentication
realm=turn.yourdomain.com

# Server name
server-name=turn.yourdomain.com

# Enable long-term credentials
lt-cred-mech

# User credentials (username:password format)
user=metlab_turn_user:your_secure_password

# Minimum and maximum port range for relay
min-port=49152
max-port=65535

# Enable verbose logging (disable in production)
verbose

# Log file
log-file=/var/log/turnserver.log

# Enable fingerprinting
fingerprint

# Disable UDP (optional, use only TCP/TLS)
# no-udp

# SSL/TLS certificates (for secure connections)
cert=/etc/letsencrypt/live/turn.yourdomain.com/fullchain.pem
pkey=/etc/letsencrypt/live/turn.yourdomain.com/privkey.pem

# Deny access to private IP ranges
no-loopback-peers
no-multicast-peers
```

#### Start Coturn

```bash
sudo systemctl start coturn
sudo systemctl status coturn
```

#### Firewall Configuration

Open required ports:

```bash
# TURN/STUN ports
sudo ufw allow 3478/tcp
sudo ufw allow 3478/udp
sudo ufw allow 5349/tcp
sudo ufw allow 5349/udp

# Relay port range
sudo ufw allow 49152:65535/tcp
sudo ufw allow 49152:65535/udp
```

#### Django Configuration

Update your `.env.production` file:

```bash
TURN_SERVER_URL=turn:turn.yourdomain.com:3478
TURN_USERNAME=metlab_turn_user
TURN_PASSWORD=your_secure_password
```

For TLS (recommended):

```bash
TURN_SERVER_URL=turns:turn.yourdomain.com:5349
TURN_USERNAME=metlab_turn_user
TURN_PASSWORD=your_secure_password
```

### Option 2: Twilio TURN Service (Easiest, Paid)

Twilio provides managed TURN servers with a simple API.

#### Setup

1. Sign up for Twilio account at https://www.twilio.com/
2. Get your Account SID and Auth Token
3. Install Twilio Python SDK:

```bash
pip install twilio
```

4. Create a helper function in `video_chat/ice_servers.py`:

```python
from twilio.rest import Client
from django.conf import settings

def get_twilio_turn_credentials():
    """Get temporary TURN credentials from Twilio"""
    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN
    )
    
    token = client.tokens.create()
    
    return {
        'iceServers': token.ice_servers,
        'ttl': 86400  # 24 hours
    }
```

5. Update `.env.production`:

```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
```

### Option 3: Xirsys (Managed TURN Service)

Xirsys provides managed TURN/STUN infrastructure.

#### Setup

1. Sign up at https://xirsys.com/
2. Create a channel for your application
3. Get your API credentials
4. Update `.env.production`:

```bash
XIRSYS_IDENT=your_ident
XIRSYS_SECRET=your_secret
XIRSYS_CHANNEL=your_channel
```

5. Fetch ICE servers dynamically using their API

## Testing Your TURN Server

### Test with Trickle ICE

Visit https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/

1. Add your TURN server URL
2. Add username and password
3. Click "Gather candidates"
4. Look for "relay" type candidates - these indicate TURN is working

### Test with Command Line

```bash
# Test TURN server connectivity
turnutils_uclient -v -u metlab_turn_user -w your_secure_password turn.yourdomain.com
```

## Security Best Practices

1. **Use Strong Credentials**: Generate random, long passwords for TURN authentication
2. **Enable TLS**: Use TURNS (TURN over TLS) for encrypted signaling
3. **Restrict Access**: Use authentication and limit access to known users
4. **Monitor Usage**: Track bandwidth and connection metrics
5. **Rate Limiting**: Implement rate limits to prevent abuse
6. **Regular Updates**: Keep Coturn and system packages updated
7. **Firewall Rules**: Only open necessary ports
8. **Log Monitoring**: Monitor logs for suspicious activity

## Cost Considerations

### Self-Hosted Coturn
- **Pros**: Full control, no per-minute charges, one-time setup
- **Cons**: Requires server maintenance, bandwidth costs
- **Estimated Cost**: $10-50/month for VPS + bandwidth

### Twilio
- **Pros**: Managed service, easy setup, reliable
- **Cons**: Pay per usage
- **Estimated Cost**: ~$0.0005 per minute per participant

### Xirsys
- **Pros**: Managed service, global infrastructure
- **Cons**: Subscription-based pricing
- **Estimated Cost**: Starting at $10/month for small usage

## Monitoring and Maintenance

### Monitor Coturn Logs

```bash
# View real-time logs
sudo tail -f /var/log/turnserver.log

# Check for errors
sudo grep ERROR /var/log/turnserver.log
```

### Monitor Bandwidth Usage

```bash
# Install vnstat for bandwidth monitoring
sudo apt-get install vnstat
sudo vnstat -i eth0
```

### Performance Tuning

For high-traffic scenarios, adjust these settings in `/etc/turnserver.conf`:

```conf
# Increase max connections
max-bps=1000000

# Optimize for high concurrency
total-quota=100
bps-capacity=0
```

## Troubleshooting

### TURN Server Not Responding

1. Check if Coturn is running: `sudo systemctl status coturn`
2. Verify firewall rules: `sudo ufw status`
3. Check logs: `sudo tail -f /var/log/turnserver.log`
4. Test connectivity: `telnet turn.yourdomain.com 3478`

### No Relay Candidates

1. Verify TURN credentials are correct
2. Check that external-ip is set correctly
3. Ensure relay ports are open in firewall
4. Test with Trickle ICE tool

### High Bandwidth Usage

1. Monitor active connections
2. Implement session time limits
3. Consider using audio-only fallback for poor connections
4. Optimize video quality settings

## References

- [Coturn Documentation](https://github.com/coturn/coturn)
- [WebRTC ICE Documentation](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Protocols)
- [Twilio TURN Service](https://www.twilio.com/docs/stun-turn)
- [Xirsys Documentation](https://docs.xirsys.com/)
