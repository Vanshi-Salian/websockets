from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: str
    email: str
    name: str
    role: str  # admin, approver, teacher, student
    department_id: Optional[str] = None
    batch_id: Optional[str] = None
    course_ids: Optional[list] = []