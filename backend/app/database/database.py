from typing import List, Dict, Optional
from datetime import datetime
import uuid

# In-memory storage for development (replace with real database)
messages_store = {}
ai_conversations_store = []

class Database:
    async def connect(self):
        """Connect to database"""
        print("Connected to database (in-memory mode)")
        return True
    
    async def disconnect(self):
        """Disconnect from database"""
        print("Disconnected from database")
        return True
    
    async def save_message(self, message: dict):
        """Save message to database"""
        conv_key = f"{message['sender_id']}_{message['recipient_id']}"
        if conv_key not in messages_store:
            messages_store[conv_key] = []
        messages_store[conv_key].append(message)
        return message
    
    async def get_conversation(self, user1: str, user2: str, limit: int = 50, offset: int = 0) -> List[dict]:
        """Get conversation between two users"""
        conv_key1 = f"{user1}_{user2}"
        conv_key2 = f"{user2}_{user1}"
        messages = messages_store.get(conv_key1, []) + messages_store.get(conv_key2, [])
        messages.sort(key=lambda x: x.get("timestamp", ""))
        return messages[offset:offset + limit]
    
    async def update_message_status(self, message_id: str, delivered: bool = None, read: bool = None):
        """Update message status"""
        for conv_key, messages in messages_store.items():
            for message in messages:
                if message.get("id") == message_id:
                    if delivered is not None:
                        message["delivered"] = delivered
                        message["delivered_at"] = datetime.now().isoformat()
                    if read is not None:
                        message["read"] = read
                        message["read_at"] = datetime.now().isoformat()
                    return True
        return False
    
    async def get_message(self, message_id: str) -> Optional[dict]:
        """Get single message by ID"""
        for conv_key, messages in messages_store.items():
            for message in messages:
                if message.get("id") == message_id:
                    return message
        return None
    
    async def mark_as_offline(self, message_id: str):
        """Mark message as offline"""
        for conv_key, messages in messages_store.items():
            for message in messages:
                if message.get("id") == message_id:
                    message["is_offline"] = True
                    return True
        return False
    
    async def get_offline_messages(self, user_id: str) -> List[dict]:
        """Get offline messages for user"""
        offline_messages = []
        for conv_key, messages in messages_store.items():
            for message in messages:
                if message.get("recipient_id") == user_id and not message.get("delivered", False):
                    offline_messages.append(message)
        return offline_messages
    
    async def mark_messages_as_read(self, message_ids: List[str], reader_id: str):
        """Mark multiple messages as read"""
        count = 0
        for message_id in message_ids:
            for conv_key, messages in messages_store.items():
                for message in messages:
                    if message.get("id") == message_id and message.get("recipient_id") == reader_id:
                        message["read"] = True
                        message["read_at"] = datetime.now().isoformat()
                        count += 1
                        break
        return count
    
    async def save_ai_conversation(self, conv_data: dict):
        """Save AI conversation"""
        conv_data["id"] = str(uuid.uuid4())
        conv_data["saved_at"] = datetime.now().isoformat()
        ai_conversations_store.append(conv_data)
        return conv_data
    
    async def save_ai_feedback(self, feedback_data: dict):
        """Save AI feedback"""
        feedback_data["id"] = str(uuid.uuid4())
        feedback_data["saved_at"] = datetime.now().isoformat()
        # Store in a separate list or same store
        return feedback_data