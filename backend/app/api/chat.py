from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# Mock database for now (replace with actual database calls)
conversations_db = {}
messages_db = {}

@router.get("/history/{other_user_id}")
async def get_chat_history(
    other_user_id: str,
    current_user_id: str = "student1",  # In production, get from JWT token
    limit: int = 50,
    offset: int = 0
):
    """Get chat history between two users"""
    conversation_key = f"{current_user_id}_{other_user_id}"
    messages = messages_db.get(conversation_key, [])
    
    # Sort by timestamp and paginate
    messages.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    paginated = messages[offset:offset + limit]
    
    return {"messages": paginated, "total": len(messages)}

@router.get("/conversations")
async def get_conversations(
    current_user_id: str = "student1"  # In production, get from JWT token
):
    """Get all conversations for current user"""
    user_conversations = []
    
    for conv_key, messages in messages_db.items():
        if current_user_id in conv_key:
            other_id = conv_key.replace(f"{current_user_id}_", "").replace(f"_{current_user_id}", "")
            
            # Get last message
            last_message = messages[-1] if messages else None
            
            user_conversations.append({
                "other_user_id": other_id,
                "other_user_name": f"User {other_id}",  # Fetch from user service
                "last_message": last_message,
                "last_message_time": last_message.get("timestamp") if last_message else None,
                "unread_count": sum(1 for m in messages if not m.get("read", False) and m.get("recipient_id") == current_user_id),
                "role": "student"  # Fetch from user service
            })
    
    return {"conversations": user_conversations}

@router.post("/messages/read")
async def mark_messages_read(
    message_ids: List[str],
    current_user_id: str = "student1"
):
    """Mark messages as read"""
    for conv_key, messages in messages_db.items():
        for message in messages:
            if message.get("id") in message_ids:
                message["read"] = True
                message["read_at"] = datetime.now().isoformat()
    
    return {"success": True, "message_ids": message_ids}