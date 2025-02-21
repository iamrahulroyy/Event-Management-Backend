from pydantic import BaseModel
from typing import Optional

from DB.models import rsvpenum

class EventRequest(BaseModel):
    organizer_name: str
    event_id:int
    title: str
    description: str
    budget: float
    event_date: str = "d/m/Y"

class Register_user (BaseModel):
    organizer_name: str = "test"
    email: str = "test@example.com"
    password: str = "test123456"
    contact : str = "91+9612105975"
    name: str = "test"

class Login_user(BaseModel):
    data: Optional[str] = "test"
    password: str = "test123456"
    keepLogin: bool = True

class RSVPSubmit(BaseModel):
    event_id : int
    title :str
    username: str = "john_doe"
    status: rsvpenum

# class RSVPUpdate(BaseModel):
#     event_id: int
#     username: str
#     new_status: str = "Accepted"

