from fastapi import APIRouter, Depends, Request, HTTPException
from sqlmodel import Session
from DB.database import DataBasePool, authentication_required
from api.response.rsvp import RSVPService
from extra.datamodel import RSVPSubmit

rsvpRouter = APIRouter(prefix="/rsvp", tags=["RSVP Route"])

rsvp_service = RSVPService()

@rsvpRouter.post("/submit")
async def submit_rsvp(request: Request, data: RSVPSubmit, db_pool: Session = Depends(DataBasePool.get_pool)):
    return await rsvp_service.submit_rsvp(request, data, db_pool)

@rsvpRouter.get("/get_responses")
@authentication_required
async def get_rsvp_responses(request:Request,event_id: int, db_pool: Session = Depends(DataBasePool.get_pool)):
    return await rsvp_service.get_rsvp_responses(request,event_id, db_pool)

@rsvpRouter.put("/update")
async def update_rsvp(data: RSVPSubmit, db_pool: Session = Depends(DataBasePool.get_pool)):
    return await rsvp_service.update_rsvp(data, db_pool)

@rsvpRouter.delete("/delete")
@authentication_required
async def delete_rsvp(request:Request,event_id: int, username: str, db_pool: Session = Depends(DataBasePool.get_pool)):
    return await rsvp_service.delete_rsvp(request,event_id, username, db_pool)
