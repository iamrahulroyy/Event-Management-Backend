import csv
import time
import traceback
from sqlmodel import Session, select
from DB.database import EVENT_DB
from DB.models import RSVP, Event, TableNameEnum, rsvpenum
from extra.datamodel import RSVPSubmit
from extra.emailService import send_email_single
from extra.helper import send_json_response
from fastapi import BackgroundTasks, Request, UploadFile, status
import xml.etree.ElementTree as ET


db = EVENT_DB()


class RSVPService:
    def __init__(self):
        pass

    @staticmethod
    async def submit_rsvp(request, data: RSVPSubmit, db_pool: Session):
        try:
            event = await db.get_attr(TableNameEnum.Event, {"event_id": data.event_id}, db_pool)
            print(event)
            if not event:
                return send_json_response(message="Event not found", status=status.HTTP_404_NOT_FOUND, body={})

            if isinstance(event, list):
                event = event[0]

            existing_rsvp = await db.get_attr(TableNameEnum.RSVP,{"username": data.username, "event_id": event.id},db_pool,)

            if existing_rsvp:
                return send_json_response(
                    message="You have already submitted an RSVP. Please use the update endpoint to modify your response.",
                    status=status.HTTP_400_BAD_REQUEST,
                    body={},
                )

            new_rsvp = RSVP(
                event_id=event.id,  
                title=data.title,
                username=data.username,
                status=data.status,
                created_at=int(time.time()),
            )

            success = await db.insert(TableNameEnum.RSVP, new_rsvp.dict(), db_pool)
            if not success:
                return send_json_response(
                    message="Failed to submit RSVP",
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    body={},
                )

            return send_json_response(
                message="RSVP submitted successfully.",
                status=status.HTTP_200_OK,
                body={},
            )

        except Exception as e:
            traceback.print_exc()
            return send_json_response(
                message="Error submitting RSVP",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                body={},
            )

    @staticmethod
    async def get_rsvp_responses(request: Request, event_id: int, db_pool: Session):
        """Fetch all RSVP responses for an event."""
        try:
            results = await db.get_attr(
                TableNameEnum.RSVP, {"event_id": event_id}, db_pool
            )
            if not results:
                return send_json_response(
                    message="No RSVPs found for this event",
                    status=status.HTTP_404_NOT_FOUND,
                    body={},
                )

            return {
                "event_id": event_id,
                "responses": [rsvp.dict() for rsvp in results if rsvp is not None],
            }

        except Exception as e:
            traceback.print_exc()
            return send_json_response(
                message="Error fetching RSVPs",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                body={},
            )

    @staticmethod
    async def update_rsvp(data: RSVPSubmit, db_pool: Session):
        try:
            rsvp = await db.get_attr(TableNameEnum.RSVP,{"event_id": data.event_id, "username": data.username},db_pool,)
            if not rsvp:
                return send_json_response(message="RSVP not found", status=status.HTTP_404_NOT_FOUND, body={})

            update_data = {
                "event_id": data.event_id,
                "username": data.username,
                "status": data.status,
                "updated_at": int(time.time()),
            }

            ok = await db.update_attr(TableNameEnum.RSVP, update_data, db_pool)
            if not ok:
                return send_json_response(message="Failed to update RSVP",status=status.HTTP_500_INTERNAL_SERVER_ERROR,body={},)

            return send_json_response( message="RSVP updated successfully", status=status.HTTP_200_OK, body={})
        except Exception as e:
            traceback.print_exc()
            return send_json_response(message="Error updating RSVP",status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={},)

    @staticmethod
    async def delete_rsvp(
        request: Request, event_id: int, username: str, db_pool: Session
    ):
        """Delete an RSVP response for an event."""
        try:
            rsvp = await db.get_attr(TableNameEnum.RSVP,{"event_id": event_id, "username": username},db_pool,)

            if isinstance(rsvp, list):
                rsvp = rsvp[0] if rsvp else None

            if not rsvp:
                return send_json_response(message="RSVP not found", status=status.HTTP_404_NOT_FOUND, body={})

            success = await db.delete(rsvp, db_pool)
            if not success:
                return send_json_response(message="Failed to delete RSVP",status=status.HTTP_500_INTERNAL_SERVER_ERROR,body={},)

            return send_json_response(message="RSVP deleted successfully", status=status.HTTP_200_OK, body={})
        except Exception as e:
            traceback.print_exc()
            return send_json_response(message="Error deleting RSVP", status=status.HTTP_500_INTERNAL_SERVER_ERROR,body={},)

    @staticmethod
    async def invite_bulk(request: Request, event_id: int, file: UploadFile, background_tasks: BackgroundTasks, db_pool: Session):
        try:
            print(f"Debug - Looking up event with ID: {event_id}")
            event = await db.get_attr(TableNameEnum.Event, {"event_id": event_id}, db_pool)
            if not event: return send_json_response(message="Event not found", status=status.HTTP_404_NOT_FOUND, body={})
            if isinstance(event, list): event = event[0]
            contents = await file.read()
            rsvp_objs = []
            if file.filename.endswith(".csv"):
                rows = contents.decode("utf-8").splitlines()
                csv_reader = csv.reader(rows)
                for row in csv_reader:
                    username_or_email = row[0]
                    rsvp_obj = RSVP(event_id=event.id, username=username_or_email, title=event.title, status=rsvpenum.PENDING, created_at=int(time.time()))
                    db_pool.add(rsvp_obj)
                    db_pool.commit()
                    db_pool.refresh(rsvp_obj)
                    rsvp_objs.append(rsvp_obj)
            elif file.filename.endswith(".xml"):
                root = ET.fromstring(contents)
                for guest in root.findall("guest"):
                    username_or_email = guest.get("email")
                    rsvp_obj = RSVP(event_id=event_id, username=username_or_email, status=rsvpenum.PENDING, title=event.title, created_at=int(time.time()))
                    db_pool.add(rsvp_obj)
                    db_pool.commit()
                    db_pool.refresh(rsvp_obj)
                    rsvp_objs.append(rsvp_obj)
            else: return send_json_response(message="Unsupported file format. Only CSV/XML allowed.", status=status.HTTP_400_BAD_REQUEST, body={})
            for rsvp_obj in rsvp_objs: background_tasks.add_task(send_email_single, rsvp_obj.username, rsvp_obj.token)
            return send_json_response(message="Invitations sent successfully!", status=status.HTTP_200_OK, body={"invited_count": len(rsvp_objs)})
        except Exception as e:
            traceback.print_exc()
            return send_json_response(message="An error occurred", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={})

    @staticmethod
    async def respond_via_link(request: Request, token: str, accept: bool, db_pool: Session):
        try:
            rsvp = db_pool.exec(select(RSVP).where(RSVP.token == token)).first()
            if not rsvp: return send_json_response(message="Invalid RSVP token", status=status.HTTP_404_NOT_FOUND, body={})
            rsvp.status = rsvpenum.ACCEPTED if accept else rsvpenum.DECLINED
            db_pool.add(rsvp)
            db_pool.commit()
            return send_json_response(message=f"RSVP {rsvp.status}", status=status.HTTP_200_OK, body={"event_id": rsvp.event_id})
        except Exception as e:
            traceback.print_exc()
            return send_json_response(message="An error occurred", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={})

