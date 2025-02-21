import time
import traceback
from sqlmodel import Session, select
from DB.database import EVENT_DB
from DB.models import RSVP, Event, TableNameEnum
from extra.datamodel import RSVPSubmit
from extra.helper import send_json_response
from fastapi import Request, status


db = EVENT_DB()

class RSVPService:
    def __init__(self):
        pass

    @staticmethod
    async def submit_rsvp(request, data: RSVPSubmit, db_pool: Session):
        try:
            event = await db.get_attr(TableNameEnum.Event, {"title": data.title}, db_pool)
            if not event:
                return send_json_response(message="Event not found", status=status.HTTP_404_NOT_FOUND, body={})

            existing_rsvp = await db.get_attr(TableNameEnum.RSVP, {"username": data.username, "event_id": data.event_id}, db_pool)
            
            if existing_rsvp:
                return send_json_response(
                    message="You have already submitted an RSVP. Please use the update endpoint to modify your response.",
                    status=status.HTTP_400_BAD_REQUEST,
                    body={},
                )

            new_rsvp = RSVP(
                event_id=data.event_id,
                title=data.title,
                username=data.username,
                status=data.status,
                created_at=int(time.time()),
            )

            success = await db.insert(TableNameEnum.RSVP, new_rsvp.dict(), db_pool)
            if not success:
                return send_json_response(message="Failed to submit RSVP", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={})

            return send_json_response(message="RSVP submitted successfully", status=status.HTTP_200_OK, body={})
        
        except Exception as e:
            traceback.print_exc()
            return send_json_response(message="Error submitting RSVP", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={})


    @staticmethod
    async def get_rsvp_responses(request: Request, event_id: int, db_pool: Session):
        """Fetch all RSVP responses for an event."""
        try:
            results = await db.get_attr(TableNameEnum.RSVP, {"event_id": event_id}, db_pool)
            if not results:
                return send_json_response(message="No RSVPs found for this event", status=status.HTTP_404_NOT_FOUND, body={})

            return {"event_id": event_id, "responses": [rsvp.dict() for rsvp in results if rsvp is not None]}
        
        except Exception as e:
            traceback.print_exc()
            return send_json_response(message="Error fetching RSVPs", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={})



    @staticmethod
    async def update_rsvp(data: RSVPSubmit, db_pool: Session):
        try:
            rsvp = await db.get_attr(TableNameEnum.RSVP, {"event_id": data.event_id, "username": data.username}, db_pool)
            if not rsvp:
                return send_json_response(message="RSVP not found", status=status.HTTP_404_NOT_FOUND, body={})

            update_data = {
                "event_id": data.event_id,
                "username": data.username,
                "status": data.status,
                "updated_at": int(time.time())
            }

            ok = await db.update_attr(TableNameEnum.RSVP, update_data, db_pool)
            if not ok:
                return send_json_response(message="Failed to update RSVP", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={})

            return send_json_response(message="RSVP updated successfully", status=status.HTTP_200_OK, body={})
        
        except Exception as e:
            traceback.print_exc()
            return send_json_response(message="Error updating RSVP", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={})


    @staticmethod
    async def delete_rsvp(request:Request,event_id: int, username: str, db_pool: Session):
        """Delete an RSVP response for an event."""
        try:
            # Fetch the RSVP record
            rsvp = await db.get_attr(TableNameEnum.RSVP, {"event_id": event_id, "username": username}, db_pool)

            if isinstance(rsvp, list):
                rsvp = rsvp[0] if rsvp else None

            if not rsvp:
                return send_json_response(
                    message="RSVP not found",
                    status=status.HTTP_404_NOT_FOUND,
                    body={}
                )

            # Delete the RSVP record
            success = await db.delete(rsvp, db_pool)
            if not success:
                return send_json_response(
                    message="Failed to delete RSVP",
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    body={}
                )

            return send_json_response(
                message="RSVP deleted successfully",
                status=status.HTTP_200_OK,
                body={}
            )
        except Exception as e:
            traceback.print_exc()
            return send_json_response(
                message="Error deleting RSVP",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                body={}
            )
