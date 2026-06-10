from fastapi import WebSocket
from typing import Dict, Set, Optional
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_metadata: Dict[str, dict] = {}
        self.user_rooms: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, user_data: dict):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_metadata[user_id] = {
            "user_data": user_data,
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "rooms": set()
        }
        self.user_rooms[user_id] = set()
        
        # Join role-based room
        role = user_data.get("role")
        if role:
            await self.join_room(user_id, f"role:{role}")
        
        # Join department room
        dept_id = user_data.get("department_id")
        if dept_id:
            await self.join_room(user_id, f"dept:{dept_id}")
        
        # Join batch room for students
        batch_id = user_data.get("batch_id")
        if batch_id:
            await self.join_room(user_id, f"batch:{batch_id}")
            
        # Broadcast user online
        await self.broadcast_user_status(user_id, "online")
        print(f"✅ User {user_id} ({role}) connected. Total: {len(self.active_connections)}")
        
    def disconnect(self, user_id: str):
        """Remove disconnected user"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_metadata:
            del self.user_metadata[user_id]
        if user_id in self.user_rooms:
            del self.user_rooms[user_id]
        print(f"❌ User {user_id} disconnected. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, user_id: str) -> bool:
        """Send message to specific user"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                print(f"Error sending to {user_id}: {e}")
                self.disconnect(user_id)
                return False
        return False
    
    async def broadcast_to_role(self, message: dict, role: str) -> int:
        """Broadcast to all users with specific role"""
        count = 0
        for user_id, websocket in self.active_connections.items():
            user_role = self.user_metadata[user_id]["user_data"].get("role")
            if user_role == role:
                try:
                    await websocket.send_json(message)
                    count += 1
                except Exception as e:
                    print(f"Error broadcasting to {user_id}: {e}")
        return count
    
    async def broadcast_to_room(self, message: dict, room: str) -> int:
        """Broadcast to all users in a room"""
        count = 0
        for user_id in self.user_rooms:
            if room in self.user_rooms[user_id]:
                success = await self.send_personal_message(message, user_id)
                if success:
                    count += 1
        return count
    
    async def join_room(self, user_id: str, room: str):
        """Add user to a chat room"""
        if user_id in self.user_rooms:
            self.user_rooms[user_id].add(room)
            
    async def leave_room(self, user_id: str, room: str):
        """Remove user from a room"""
        if user_id in self.user_rooms and room in self.user_rooms[user_id]:
            self.user_rooms[user_id].remove(room)
    
    async def broadcast_user_status(self, user_id: str, status: str):
        """Broadcast user online/offline status"""
        user_meta = self.user_metadata.get(user_id, {})
        user_data = user_meta.get("user_data", {})
        
        status_message = {
            "type": "user_status",
            "payload": {
                "user_id": user_id,
                "status": status,
                "role": user_data.get("role"),
                "name": user_data.get("name", "Unknown"),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Broadcast to relevant roles
        await self.broadcast_to_room(status_message, "role:student")
        await self.broadcast_to_room(status_message, "role:teacher")
        await self.broadcast_to_room(status_message, "role:admin")
    
    async def close_all_connections(self):
        """Close all active connections"""
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.close()
            except Exception as e:
                print(f"Error closing connection for {user_id}: {e}")
        self.active_connections.clear()
        self.user_metadata.clear()
        self.user_rooms.clear()
    
    def get_online_users(self) -> list:
        """Get list of online users"""
        online_users = []
        for user_id, metadata in self.user_metadata.items():
            online_users.append({
                "user_id": user_id,
                "name": metadata["user_data"].get("name"),
                "role": metadata["user_data"].get("role"),
                "connected_at": metadata["connected_at"].isoformat()
            })
        return online_users
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if user is online"""
        return user_id in self.active_connections