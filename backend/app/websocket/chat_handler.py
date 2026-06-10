from datetime import datetime
import uuid
from app.websocket.connection_manager import ConnectionManager
from app.database.database import Database
from app.services.auth_service import AuthService

class ChatHandler:
    def __init__(self, connection_manager: ConnectionManager, database: Database, auth_service: AuthService):
        self.connection_manager = connection_manager
        self.database = database
        self.auth_service = auth_service
        
    async def handle_chat_message(self, sender_id: str, message: dict):
        """Handle direct chat between two users"""
        payload = message.get("payload", {})
        recipient_id = payload.get("recipient_id")
        message_type = payload.get("message_type", "text")
        content = payload.get("content")
        
        print(f"📨 Chat message from {sender_id} to {recipient_id}: {content}")
        
        if not recipient_id:
            await self.send_error(sender_id, "recipient_id required")
            return
        
        # Get sender info from user_metadata
        sender_meta = self.connection_manager.user_metadata.get(sender_id, {})
        sender_data = sender_meta.get("user_data", {})
        
        print(f"Sender data: {sender_data}")
        
        # Create message object with proper sender name
        chat_message = {
            "id": str(uuid.uuid4()),
            "sender_id": sender_id,
            "sender_name": sender_data.get("name", sender_id),
            "sender_role": sender_data.get("role", "user"),
            "recipient_id": recipient_id,
            "message_type": message_type,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "read": False,
            "delivered": False,
            "is_offline": False
        }
        
        print(f"Created message: {chat_message}")
        
        # Store in database
        await self.database.save_message(chat_message)
        
        # Check if recipient is online
        is_recipient_online = self.connection_manager.is_user_online(recipient_id)
        print(f"Recipient {recipient_id} online: {is_recipient_online}")
        
        # Send to recipient if online
        if is_recipient_online:
            delivered = await self.connection_manager.send_personal_message(
                {"type": "chat_message", "payload": chat_message},
                recipient_id
            )
            if delivered:
                print(f"✅ Message delivered to {recipient_id}")
                chat_message["delivered"] = True
                chat_message["delivered_at"] = datetime.now().isoformat()
                await self.database.update_message_status(chat_message["id"], delivered=True)
            else:
                print(f"❌ Failed to deliver message to {recipient_id}")
        else:
            # Store as offline message
            await self.database.mark_as_offline(chat_message["id"])
            chat_message["is_offline"] = True
            print(f"📦 Message stored as offline for {recipient_id}")
        
        # Send delivery receipt to sender
        await self.connection_manager.send_personal_message(
            {
                "type": "message_status",
                "payload": {
                    "message_id": chat_message["id"],
                    "status": "delivered" if is_recipient_online else "stored",
                    "recipient_online": is_recipient_online,
                    "timestamp": datetime.now().isoformat()
                }
            },
            sender_id
        )
    
    async def handle_typing_indicator(self, sender_id: str, message: dict):
        """Handle typing indicators"""
        payload = message.get("payload", {})
        recipient_id = payload.get("recipient_id")
        is_typing = payload.get("is_typing", False)
        
        if self.connection_manager.is_user_online(recipient_id):
            await self.connection_manager.send_personal_message(
                {
                    "type": "typing_indicator",
                    "payload": {
                        "user_id": sender_id,
                        "is_typing": is_typing,
                        "timestamp": datetime.now().isoformat()
                    }
                },
                recipient_id
            )
    
    async def handle_read_receipt(self, reader_id: str, message: dict):
        """Handle read receipts"""
        payload = message.get("payload", {})
        message_ids = payload.get("message_ids", [])
        
        if not message_ids:
            return
        
        await self.database.mark_messages_as_read(message_ids, reader_id)
        
        # Notify sender
        for message_id in message_ids:
            msg = await self.database.get_message(message_id)
            if msg and self.connection_manager.is_user_online(msg["sender_id"]):
                await self.connection_manager.send_personal_message(
                    {
                        "type": "read_receipt",
                        "payload": {
                            "message_id": message_id,
                            "read_by": reader_id,
                            "read_at": datetime.now().isoformat()
                        }
                    },
                    msg["sender_id"]
                )
    
    async def send_offline_messages(self, user_id: str):
        """Send stored offline messages"""
        offline_messages = await self.database.get_offline_messages(user_id)
        print(f"📬 Sending {len(offline_messages)} offline messages to {user_id}")
        
        for message in offline_messages:
            await self.database.update_message_status(message["id"], delivered=True)
            await self.connection_manager.send_personal_message(
                {"type": "chat_message", "payload": message},
                user_id
            )
            
            if self.connection_manager.is_user_online(message["sender_id"]):
                await self.connection_manager.send_personal_message(
                    {
                        "type": "message_status",
                        "payload": {
                            "message_id": message["id"],
                            "status": "delivered",
                            "delivered_at": datetime.now().isoformat()
                        }
                    },
                    message["sender_id"]
                )
    
    async def broadcast_user_status(self, user_id: str, status: str):
        """Broadcast user status"""
        await self.connection_manager.broadcast_user_status(user_id, status)
    
    async def send_error(self, user_id: str, error_message: str):
        """Send error message"""
        await self.connection_manager.send_personal_message(
            {
                "type": "error",
                "payload": {"error": error_message, "timestamp": datetime.now().isoformat()}
            },
            user_id
        )