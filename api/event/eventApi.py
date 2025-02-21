from fastapi import APIRouter, Depends, Request
from DB.database import DataBasePool, authentication_required
from DB.models import Event
from sqlalchemy.orm import Session

from api.event import EventService
from extra.datamodel import EventRequest


router = APIRouter(prefix="/events", tags=["Events"])

event = EventService()


@router.post("/create_event")
@authentication_required
async def create_event(request: Request,data:EventRequest,db_pool: Session = Depends(DataBasePool.get_pool),):
    return await event.save_event(request,data,db_pool)

@router.get("/get_event")
@authentication_required
async def get_event(request: Request, username:str,db_pool: Session = Depends(DataBasePool.get_pool),):
    return await event.get_event(request,username, db_pool)

@router.post("/update_event")
@authentication_required
async def update_event(request: Request,data:EventRequest,db_pool: Session = Depends(DataBasePool.get_pool),):
    return await event.update_event(request,data,db_pool)

@router.delete("/delete_event")
@authentication_required
async def delete_event(request: Request,organizer_name:str,title:str,db_pool: Session = Depends(DataBasePool.get_pool),):
    return await event.delete_event(request,organizer_name, title,db_pool)
