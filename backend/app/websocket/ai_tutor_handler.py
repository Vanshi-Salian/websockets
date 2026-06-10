from datetime import datetime
import uuid
import asyncio
from app.websocket.connection_manager import ConnectionManager
from app.database.database import Database

class AITutorHandler:
    def __init__(self, connection_manager: ConnectionManager, database: Database):
        self.connection_manager = connection_manager
        self.database = database
        self.active_sessions = {}
        
    async def handle_ai_query(self, user_id: str, message: dict):
        """Handle AI tutor queries with streaming"""
        payload = message.get("payload", {})
        query = payload.get("query")
        session_id = payload.get("session_id", user_id)
        context = payload.get("context", {})
        
        # Create or get session
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                "user_id": user_id,
                "messages": [],
                "created_at": datetime.now()
            }
        
        # Add user message
        user_message = {
            "role": "user",
            "content": query,
            "timestamp": datetime.now().isoformat()
        }
        self.active_sessions[session_id]["messages"].append(user_message)
        
        # Send acknowledgment
        await self.connection_manager.send_personal_message(
            {
                "type": "ai_ack",
                "payload": {
                    "session_id": session_id,
                    "status": "processing",
                    "timestamp": datetime.now().isoformat()
                }
            },
            user_id
        )
        
        # Simulate AI response (replace with actual AI)
        await self.simulate_ai_response(user_id, query, session_id, context)
    
    async def simulate_ai_response(self, user_id: str, query: str, session_id: str, context: dict):
        """Simulate streaming AI response"""
        sample_responses = {
            "schedule": "Based on your schedule, you have classes from Monday to Friday. Your next class is at 10 AM tomorrow.",
            "assignment": f"You have pending assignments. The deadline for the current assignment is in 3 days.",
            "grade": "Your current overall grade is 85%. You're doing great! Keep it up.",
            "default": f"I understand your question about '{query}'. In our smart classroom system, you can access all learning materials easily."
        }
        
        response_text = sample_responses.get("default")
        for key in sample_responses:
            if key in query.lower():
                response_text = sample_responses[key]
                break
        
        # Stream chunks
        chunks = response_text.split(" ")
        full_response = ""
        
        for i, chunk in enumerate(chunks):
            full_response += chunk + (" " if i < len(chunks) - 1 else "")
            
            await self.connection_manager.send_personal_message(
                {
                    "type": "ai_stream_chunk",
                    "payload": {
                        "session_id": session_id,
                        "chunk": chunk + " ",
                        "partial_response": full_response,
                        "progress": (i + 1) / len(chunks) * 100
                    }
                },
                user_id
            )
            await asyncio.sleep(0.1)
        
        # Save to database
        await self.database.save_ai_conversation({
            "user_id": user_id,
            "session_id": session_id,
            "query": query,
            "response": full_response,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
        
        # Send completion
        await self.connection_manager.send_personal_message(
            {
                "type": "ai_complete",
                "payload": {
                    "session_id": session_id,
                    "full_response": full_response,
                    "message_count": len(self.active_sessions[session_id]["messages"])
                }
            },
            user_id
        )
    
    async def handle_ai_feedback(self, user_id: str, message: dict):
        """Handle user feedback on AI responses"""
        payload = message.get("payload", {})
        session_id = payload.get("session_id")
        message_id = payload.get("message_id")
        feedback = payload.get("feedback")
        
        await self.database.save_ai_feedback({
            "user_id": user_id,
            "session_id": session_id,
            "message_id": message_id,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })
        
        await self.connection_manager.send_personal_message(
            {
                "type": "ai_feedback_ack",
                "payload": {
                    "message_id": message_id,
                    "feedback_received": True,
                    "thank_you": "Thanks for your feedback!"
                }
            },
            user_id
        )