import jwt
from datetime import datetime, timedelta
from typing import Optional
import os

class AuthService:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET", "your-secret-key")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        
    async def authenticate_websocket(self, token: Optional[str], user_id: str) -> Optional[dict]:
        """Authenticate WebSocket connection"""
        if not token:
            # For development - remove in production
            return self.get_mock_user(user_id)
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("user_id") != user_id:
                return None
            
            return {
                "id": user_id,
                "email": payload.get("email"),
                "name": payload.get("name"),
                "role": payload.get("role"),
                "department_id": payload.get("department_id"),
                "batch_id": payload.get("batch_id"),
                "course_ids": payload.get("course_ids", [])
            }
        except jwt.InvalidTokenError:
            return None
    
    def generate_token(self, user_data: dict) -> str:
        """Generate JWT token"""
        payload = {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "role": user_data["role"],
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def get_mock_user(self, user_id: str) -> dict:
        """Get mock user for development"""
        mock_users = {
            "student1": {
                "id": "student1",
                "email": "student@example.com",
                "name": "John Student",  # Make sure name is set
                "role": "student",
                "department_id": "cse",
                "batch_id": "2024",
                "course_ids": ["math101", "cs101"]
            },
            "teacher1": {
                "id": "teacher1",
                "email": "teacher@example.com",
                "name": "Jane Teacher",  # Make sure name is set
                "role": "teacher",
                "department_id": "cse",
                "batch_id": None,
                "course_ids": ["math101", "cs101"]
            },
            "admin1": {
                "id": "admin1",
                "email": "admin@example.com",
                "name": "Admin User",
                "role": "admin",
                "department_id": None,
                "batch_id": None,
                "course_ids": []
            }
        }
        return mock_users.get(user_id, mock_users["student1"])