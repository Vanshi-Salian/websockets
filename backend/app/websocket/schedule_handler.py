from datetime import datetime
from app.websocket.connection_manager import ConnectionManager

class ScheduleHandler:
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        
    async def handle_schedule_message(self, user_id: str, message: dict):
        """Handle schedule-related messages"""
        payload = message.get("payload", {})
        action = payload.get("action")
        
        if action == "validate_slot":
            await self.validate_slot(user_id, payload)
        elif action == "get_schedule":
            await self.get_schedule(user_id, payload)
    
    async def validate_slot(self, user_id: str, payload: dict):
        """Validate time slot"""
        slot_data = payload.get("slot_data", {})
        
        # Mock validation
        conflicts = self.check_conflicts(slot_data)
        
        if not conflicts:
            await self.connection_manager.send_personal_message(
                {
                    "type": "schedule_validation",
                    "payload": {
                        "is_valid": True,
                        "slot_data": slot_data,
                        "alternatives": self.generate_alternatives(slot_data)
                    }
                },
                user_id
            )
        else:
            await self.connection_manager.send_personal_message(
                {
                    "type": "schedule_conflict",
                    "payload": {
                        "is_valid": False,
                        "conflicts": conflicts,
                        "slot_data": slot_data
                    }
                },
                user_id
            )
    
    async def get_schedule(self, user_id: str, payload: dict):
        """Get user schedule"""
        user_meta = self.connection_manager.user_metadata.get(user_id, {})
        user_data = user_meta.get("user_data", {})
        
        schedule = {
            "user_id": user_id,
            "role": user_data.get("role"),
            "schedule": self.generate_mock_schedule(user_data.get("role")),
            "week": payload.get("week", "current")
        }
        
        await self.connection_manager.send_personal_message(
            {"type": "schedule_data", "payload": schedule},
            user_id
        )
    
    def check_conflicts(self, slot_data: dict) -> list:
        """Check for scheduling conflicts"""
        conflicts = []
        # Add your conflict detection logic here
        return conflicts
    
    def generate_alternatives(self, slot_data: dict) -> list:
        """Generate alternative slots"""
        return [
            {"day": "Monday", "time": "14:00", "room": "Room 101"},
            {"day": "Tuesday", "time": "11:00", "room": "Room 102"}
        ]
    
    def generate_mock_schedule(self, role: str) -> list:
        """Generate mock schedule"""
        if role == "student":
            return [
                {"day": "Monday", "time": "09:00-11:00", "course": "Mathematics", "room": "Hall A"},
                {"day": "Tuesday", "time": "10:00-12:00", "course": "Physics", "room": "Lab B"}
            ]
        elif role == "teacher":
            return [
                {"day": "Monday", "time": "09:00-11:00", "course": "Mathematics", "batch": "CS-A"},
                {"day": "Tuesday", "time": "10:00-12:00", "course": "Physics", "batch": "CS-B"}
            ]
        return []