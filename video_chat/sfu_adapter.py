"""
Janus SFU Adapter for Video Chat System
Provides integration with Janus Gateway for scalable group video sessions.
"""
import requests
import json
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class JanusAdapter:
    """
    Adapter for Janus SFU integration.
    Handles room creation, destruction, and participant management.
    """
    
    def __init__(self):
        self.janus_url = getattr(settings, 'JANUS_SERVER_URL', 'http://localhost:8088/janus')
        self.admin_url = getattr(settings, 'JANUS_ADMIN_URL', 'http://localhost:7088/admin')
        self.api_secret = getattr(settings, 'JANUS_API_SECRET', '')
        self.admin_secret = getattr(settings, 'JANUS_ADMIN_SECRET', '')
    
    def create_session(self):
        """
        Create a Janus session.
        Returns session_id on success.
        """
        try:
            payload = {
                "janus": "create",
                "transaction": self._generate_transaction_id()
            }
            
            if self.api_secret:
                payload["apisecret"] = self.api_secret
            
            response = requests.post(
                self.janus_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("janus") == "success":
                session_id = data.get("data", {}).get("id")
                logger.info(f"Created Janus session: {session_id}")
                return session_id
            else:
                logger.error(f"Failed to create Janus session: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Janus session: {str(e)}")
            return None
    
    def attach_plugin(self, session_id, plugin="janus.plugin.videoroom"):
        """
        Attach to a Janus plugin.
        Returns handle_id on success.
        """
        try:
            payload = {
                "janus": "attach",
                "plugin": plugin,
                "transaction": self._generate_transaction_id()
            }
            
            if self.api_secret:
                payload["apisecret"] = self.api_secret
            
            response = requests.post(
                f"{self.janus_url}/{session_id}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("janus") == "success":
                handle_id = data.get("data", {}).get("id")
                logger.info(f"Attached to plugin {plugin}: handle {handle_id}")
                return handle_id
            else:
                logger.error(f"Failed to attach plugin: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Error attaching plugin: {str(e)}")
            return None
    
    def create_room(self, room_id, description="", max_publishers=30, 
                   bitrate=1024000, record=False):
        """
        Create a VideoRoom in Janus.
        
        Args:
            room_id: Unique room identifier (use session UUID)
            description: Room description
            max_publishers: Maximum number of publishers (participants)
            bitrate: Maximum bitrate in bps (default 1 Mbps)
            record: Whether to enable recording
            
        Returns:
            dict with room details on success, None on failure
        """
        try:
            # Create session and attach plugin
            session_id = self.create_session()
            if not session_id:
                return None
            
            handle_id = self.attach_plugin(session_id)
            if not handle_id:
                return None
            
            # Create room
            payload = {
                "janus": "message",
                "transaction": self._generate_transaction_id(),
                "body": {
                    "request": "create",
                    "room": int(str(room_id).replace('-', '')[:15]),  # Convert UUID to int
                    "description": description or f"Video Session {room_id}",
                    "publishers": max_publishers,
                    "bitrate": bitrate,
                    "fir_freq": 10,
                    "audiocodec": "opus",
                    "videocodec": "vp8,vp9,h264",
                    "record": record,
                    "rec_dir": f"/opt/janus/recordings/{room_id}" if record else None
                }
            }
            
            if self.api_secret:
                payload["apisecret"] = self.api_secret
            
            response = requests.post(
                f"{self.janus_url}/{session_id}/{handle_id}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("janus") == "success" or data.get("plugindata", {}).get("data", {}).get("videoroom") == "created":
                logger.info(f"Created Janus room: {room_id}")
                
                # Cache session and handle IDs for later use
                cache.set(f"janus_room_{room_id}", {
                    "session_id": session_id,
                    "handle_id": handle_id,
                    "room_id": room_id
                }, timeout=86400)  # 24 hours
                
                return {
                    "room_id": room_id,
                    "session_id": session_id,
                    "handle_id": handle_id,
                    "janus_url": self.janus_url
                }
            else:
                logger.error(f"Failed to create room: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Janus room: {str(e)}")
            return None
    
    def destroy_room(self, room_id):
        """
        Destroy a VideoRoom in Janus.
        
        Args:
            room_id: Room identifier
            
        Returns:
            True on success, False on failure
        """
        try:
            # Get cached session info
            room_info = cache.get(f"janus_room_{room_id}")
            if not room_info:
                logger.warning(f"No cached info for room {room_id}")
                return False
            
            session_id = room_info["session_id"]
            handle_id = room_info["handle_id"]
            
            # Destroy room
            payload = {
                "janus": "message",
                "transaction": self._generate_transaction_id(),
                "body": {
                    "request": "destroy",
                    "room": int(str(room_id).replace('-', '')[:15])
                }
            }
            
            if self.api_secret:
                payload["apisecret"] = self.api_secret
            
            response = requests.post(
                f"{self.janus_url}/{session_id}/{handle_id}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("janus") == "success" or data.get("plugindata", {}).get("data", {}).get("videoroom") == "destroyed":
                logger.info(f"Destroyed Janus room: {room_id}")
                
                # Clean up cache
                cache.delete(f"janus_room_{room_id}")
                
                return True
            else:
                logger.error(f"Failed to destroy room: {data}")
                return False
                
        except Exception as e:
            logger.error(f"Error destroying Janus room: {str(e)}")
            return False
    
    def list_rooms(self):
        """
        List all active rooms in Janus.
        
        Returns:
            list of room dictionaries
        """
        try:
            session_id = self.create_session()
            if not session_id:
                return []
            
            handle_id = self.attach_plugin(session_id)
            if not handle_id:
                return []
            
            payload = {
                "janus": "message",
                "transaction": self._generate_transaction_id(),
                "body": {
                    "request": "list"
                }
            }
            
            if self.api_secret:
                payload["apisecret"] = self.api_secret
            
            response = requests.post(
                f"{self.janus_url}/{session_id}/{handle_id}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            rooms = data.get("plugindata", {}).get("data", {}).get("list", [])
            return rooms
            
        except Exception as e:
            logger.error(f"Error listing rooms: {str(e)}")
            return []
    
    def get_room_info(self, room_id):
        """
        Get information about a specific room.
        
        Args:
            room_id: Room identifier
            
        Returns:
            dict with room info on success, None on failure
        """
        try:
            room_info = cache.get(f"janus_room_{room_id}")
            if not room_info:
                return None
            
            session_id = room_info["session_id"]
            handle_id = room_info["handle_id"]
            
            payload = {
                "janus": "message",
                "transaction": self._generate_transaction_id(),
                "body": {
                    "request": "listparticipants",
                    "room": int(str(room_id).replace('-', '')[:15])
                }
            }
            
            if self.api_secret:
                payload["apisecret"] = self.api_secret
            
            response = requests.post(
                f"{self.janus_url}/{session_id}/{handle_id}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            participants = data.get("plugindata", {}).get("data", {}).get("participants", [])
            
            return {
                "room_id": room_id,
                "participants": participants,
                "participant_count": len(participants)
            }
            
        except Exception as e:
            logger.error(f"Error getting room info: {str(e)}")
            return None
    
    def enable_recording(self, room_id):
        """
        Enable recording for a room.
        
        Args:
            room_id: Room identifier
            
        Returns:
            True on success, False on failure
        """
        try:
            room_info = cache.get(f"janus_room_{room_id}")
            if not room_info:
                return False
            
            session_id = room_info["session_id"]
            handle_id = room_info["handle_id"]
            
            payload = {
                "janus": "message",
                "transaction": self._generate_transaction_id(),
                "body": {
                    "request": "enable_recording",
                    "room": int(str(room_id).replace('-', '')[:15]),
                    "record": True
                }
            }
            
            if self.api_secret:
                payload["apisecret"] = self.api_secret
            
            response = requests.post(
                f"{self.janus_url}/{session_id}/{handle_id}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            response.raise_for_status()
            logger.info(f"Enabled recording for room: {room_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling recording: {str(e)}")
            return False
    
    def _generate_transaction_id(self):
        """Generate a unique transaction ID"""
        import uuid
        return str(uuid.uuid4())
    
    def health_check(self):
        """
        Check if Janus server is healthy.
        
        Returns:
            dict with health status
        """
        try:
            response = requests.get(
                f"{self.janus_url}/info",
                timeout=5
            )
            
            response.raise_for_status()
            data = response.json()
            
            return {
                "healthy": True,
                "version": data.get("version_string", "unknown"),
                "name": data.get("name", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Janus health check failed: {str(e)}")
            return {
                "healthy": False,
                "error": str(e)
            }


# Singleton instance
_janus_adapter = None

def get_janus_adapter():
    """Get or create Janus adapter instance"""
    global _janus_adapter
    if _janus_adapter is None:
        _janus_adapter = JanusAdapter()
    return _janus_adapter
