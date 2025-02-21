from datetime import datetime
import traceback
from fastapi import  Request, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from DB.database import EVENT_DB
from DB.models import Event, TableNameEnum
from extra.datamodel import EventRequest
from extra.helper import send_json_response


db = EVENT_DB

class EventService:
    def __init__(self):
        pass


    @staticmethod
    async def save_event(request: Request, data:EventRequest,db_pool: Session):
        try:
            logged_in_user = request.state.org.organizer_name
            if logged_in_user != data.organizer_name:
                return send_json_response(message="organizer name invalid", status=status.HTTP_403_FORBIDDEN, body={})

            event_date_dt = datetime.strptime(data.event_date, "%d/%m/%Y")
            event_date_timestamp = int(event_date_dt.timestamp())
            
            event_data = {
                "event_id" : data.event_id,
                "organizer_name": data.organizer_name.lower(),
                "title": data.title,
                "description": data.description,
                "budget": data.budget,
                "event_date": event_date_timestamp
            }

            inserted_event, success = await db.insert(TableNameEnum.Event, event_data, db_pool)
            if not inserted_event:
                return send_json_response(message="Failed to insert event", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={})

            serialized_inserted_event = jsonable_encoder(inserted_event)
            return send_json_response(message="event created", status=status.HTTP_200_OK, body=serialized_inserted_event)

        except Exception as e:
            print(f"Error creating event: {e}")
            return send_json_response(message="Event not created", status=status.HTTP_404_NOT_FOUND, body={})

    @staticmethod
    async def get_event(request: Request, organizer_name: str, db_pool: Session):
        try:
            events = await db.get_attr(TableNameEnum.Event, {"organizer_name": organizer_name}, db_pool)
            if not events:
                return send_json_response(message="No events found", status=status.HTTP_404_NOT_FOUND, body=[])
            
            # Convert all events to the required format
            events_data = []
            for event in events:
                event_data = {
                    "event_id": event.event_id,
                    "organizer_name": event.organizer_name,
                    "title": event.title,
                    "description": event.description,
                    "budget": event.budget,
                    "event_date": event.event_date
                }
                events_data.append(event_data)
            
            return events_data

        except Exception as e:
            traceback.print_exc()
            return send_json_response(message="Error fetching events", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body=[])
        
    @staticmethod
    async def update_event(request: Request, data: EventRequest, db_pool: Session):
        try:
            cur_user = request.state.org
            if not cur_user:
                return send_json_response(message="User not logged in", status=status.HTTP_400_BAD_REQUEST, body={})

            if cur_user.organizer_name != data.organizer_name:
                return send_json_response(message="Username does not match", status=status.HTTP_403_FORBIDDEN, body={})

            existing_event = await db.get_attr(TableNameEnum.Event, {"organizer_name": data.organizer_name}, db_pool)
            if not existing_event:
                return send_json_response(message="Event not found", status=status.HTTP_404_NOT_FOUND, body={})

            event_date_dt = datetime.strptime(data.event_date, "%d/%m/%Y")
            event_date_timestamp = int(event_date_dt.timestamp())

            update_data = {
                "organizer_name": data.organizer_name,
                "event_id": data.event_id,
                "title": data.title,
                "description": data.description,
                "budget": data.budget,
                "event_date": event_date_timestamp
            }

            print("Update Data:", update_data)  # Log update data

            ok = await db.update_attr(TableNameEnum.Event, update_data, db_pool)
            if not ok:
                return send_json_response(message="Error updating event", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={})

            print("Update successful:", ok)

            updated_event = await db.get_attr(TableNameEnum.Event, {"organizer_name": data.organizer_name}, db_pool)

            if not updated_event:
                print("Updated event not found.")  # Log if the updated event isn't found
                return send_json_response(message="Updated event not found", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={})

            serialized_updated_event = jsonable_encoder(updated_event)

            return send_json_response(message="Updated", status=status.HTTP_200_OK, body=serialized_updated_event)

        except Exception as e:
            traceback.print_exc()
            return send_json_response(message="Error updating event", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={})



    @staticmethod
    async def delete_event(request: Request, organizer_name: str, title: str, db_pool: Session):
        try:
            cur_user = request.state.org
            if not cur_user != organizer_name:
                return send_json_response(message="username doesnot match", status=status.HTTP_400_BAD_REQUEST, body={})
            
            events = await db.get_attr(TableNameEnum.Event, {"organizer_name": organizer_name, "title": title}, db_pool)

            if not events:
                return send_json_response(message="Event not found", status=status.HTTP_404_NOT_FOUND, body={})

            # event = events[0] 

            deletion_result = await db.delete(events, db_pool)
            if not deletion_result:
                return send_json_response(message="Error deleting event", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={})

            return send_json_response(message="Event deleted", status=status.HTTP_200_OK, body={})

        except Exception as e:
            traceback.print_exc()
            return send_json_response(message="Error deleting event", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={})

