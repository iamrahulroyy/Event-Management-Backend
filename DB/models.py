from enum import Enum
import time
from sqlalchemy import Column, Integer, func
from sqlmodel import SQLModel, Field
from typing import Optional

class TableNameEnum(str, Enum):
    Event = "event"
    RSVP = "rsvp"
    ORGANIZER = "organizer"
    ORGANIZER_DETAILS = "organizer_details"
    ORGANIZER_SESSION = "organizer_session"
    ORGANIZER_META = "organizer_meta"


class rsvpenum(str, Enum):
    ACCEPTED = "accepted"
    DECLINED = "declined"

class ORGANIZER_METAReasonEnum(str, Enum):
    SIGNUP = "signup" 
    LOGIN = "login"



class ORGANIZER(SQLModel, table=True):
    id: int = Field(primary_key=True)
    organizer_name: str = Field(unique=True)
    email: str
    contact: str
    password: str
    name: Optional[str] = Field(default=None)
    created_at: Optional[int] = Field(default_factory=lambda: int(time.time()))
    updated_at: Optional[int] = Field(default=None,sa_column=Column(Integer, onupdate=func.extract("epoch", func.now())),)


class ORGANIZER_DETAILS(SQLModel, table=True):
    id: int = Field(primary_key=True)
    organizer_name: str = Field(foreign_key="organizer.organizer_name")
    email: str
    contact: Optional[int] 


class ORGANIZER_SESSION(SQLModel, table=True):
    pk: str = Field(primary_key=True)
    organizer_name: str = Field(foreign_key="organizer.organizer_name")
    ip: Optional[str]
    browser: Optional[str]
    os: Optional[str]
    created_at: int = Field(default_factory=lambda: int(time.time()))
    expired_at: int

class ORGANIZER_META(SQLModel, table=True):
    pk: int = Field(primary_key=True)
    organizer_name: str
    reason: ORGANIZER_METAReasonEnum = Field(default = ORGANIZER_METAReasonEnum.SIGNUP)
    ip : Optional[str]
    country : Optional[str] = Field(default=None)
    os: Optional[str]
    created_at: Optional[int] = Field(default_factory=lambda: int(time.time()))

class Event(SQLModel, table=True):  
    id: Optional[int] = Field(default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True))
    organizer_name: str = Field(nullable=False)
    event_id : int
    title: str 
    description: Optional[str] = None
    event_date: int = Field(default_factory=lambda: int(time.time()))
    budget: float
    updated_at: Optional[int] = Field(default=None, sa_column=Column(Integer, onupdate=func.extract("epoch", func.now())))
    created_at: Optional[int] = Field(default_factory=lambda: int(time.time()))

class RSVP(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int  = Field(foreign_key="event.id")
    username: str
    title : str
    # email: Optional[str]
    # contact: Optional[int]
    status: rsvpenum = Field(default=rsvpenum.DECLINED)  
    created_at: Optional[int] = Field(default_factory=lambda: int(time.time()))
    updated_at: Optional[int] = Field(default=None,sa_column=Column(Integer, onupdate=func.extract("epoch", func.now())),)

