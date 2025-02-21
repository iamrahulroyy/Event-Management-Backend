from functools import wraps
import time
from fastapi import Request,status
from sqlmodel import SQLModel, create_engine, Session, delete, select
from typing import Optional
import traceback
from DB.models import ORGANIZER, ORGANIZER_DETAILS, ORGANIZER_META, ORGANIZER_SESSION, RSVP, Event, TableNameEnum
from extra import variables
from extra.helper import send_json_response


class UninitializedDatabasePoolError(Exception):
    def __init__(self, message="The database connection pool has not been properly initialized. Please ensure setup is called"):
        self.message = message
        super().__init__(self.message)


class DataBasePool:
    _db_pool: Session = None
    _engine = None
    _timeout: Optional[float] = None

    @classmethod
    async def initDB(cls):
        """Initializes the database by creating the tables if not already present."""
        if cls._engine is None:
            raise UninitializedDatabasePoolError("Database engine is not initialized.")
        initDB(cls._engine)

    @classmethod
    async def getEngine(cls):
        """Returns the database engine."""
        if cls._engine is None:
            raise UninitializedDatabasePoolError("Database engine is not initialized.")
        return cls._engine

    @classmethod
    async def setup(cls, timeout: Optional[float] = None):
        """Sets up the database engine and pool."""
        if cls._engine is None:
            cls._engine = create_engine(
                variables.DATABASE_URL, pool_size=20, pool_pre_ping=True, pool_recycle=60
            )
            cls._timeout = timeout
            cls._db_pool = Session(cls._engine)
            initDB(cls._engine) 

    @classmethod
    async def get_pool(cls) -> Session:
        """Returns the current database pool session."""
        if cls._db_pool is None:
            raise UninitializedDatabasePoolError()
        return cls._db_pool

    @classmethod
    async def teardown(cls):
        """Closes the database pool."""
        if cls._db_pool is None:
            raise UninitializedDatabasePoolError()
        cls._db_pool.close()
        cls._db_pool = None 
        print("Database pool closed.")

def initDB(_engine):
    try:
        SQLModel.metadata.create_all(_engine)
    except Exception as e:
        traceback.print_exc()
        print(f"Error in creating/init tables: {e}")


class EVENT_DB:

    def __init__(self):
        pass

    @classmethod
    async def insert(cls, dbclassnam: TableNameEnum, data: dict, db_pool: Session):
        try:
            if dbclassnam == TableNameEnum.ORGANIZER:
                data = ORGANIZER(**data)
            elif dbclassnam == TableNameEnum.ORGANIZER_DETAILS:
                data = ORGANIZER_DETAILS(**data)
            elif dbclassnam == TableNameEnum.ORGANIZER_SESSION:
                data = ORGANIZER_SESSION(**data)
            elif dbclassnam == TableNameEnum.ORGANIZER_META:
                data = ORGANIZER_META(**data)
            elif dbclassnam == TableNameEnum.Event:
                data = Event(**data)
            elif dbclassnam == TableNameEnum.RSVP:
                data = RSVP(**data)
            else:
                return None, False
            
            db_pool.add(data)
            db_pool.commit()
            db_pool.refresh(data)

            return data, True
        except Exception as e:
            db_pool.rollback()
            traceback.print_exc()
            return None, False
        
    @classmethod
    async def get_attr(self, dbClassNam: TableNameEnum, data=None, db_pool: Session = None):
        try:
            # print(f"Inside get_attr, class: {dbClassNam}, data: {data}") 
            table = None

            if dbClassNam == TableNameEnum.ORGANIZER:
                statement = select(ORGANIZER).filter(ORGANIZER.organizer_name == data.get("organizer_name"))
                table = db_pool.exec(statement).all()
            
            elif dbClassNam == TableNameEnum.Event:
                if "title" in data:
                    statement = select(Event).filter(Event.title == data.get("title"))
                    table = db_pool.exec(statement).first() 
                elif "organizer_name" in data:
                    statement = select(Event).filter(Event.organizer_name == data.get("organizer_name"))
                    table = db_pool.exec(statement).all()
            
            elif dbClassNam == TableNameEnum.RSVP:
                statement = select(RSVP).filter(RSVP.event_id == data.get("event_id"))
                # print(f"SQL Statement: {str(statement)}")  
                table = db_pool.exec(statement).all()  
                # print(f"Query result for RSVP: {table}") 
            
            return table

        except Exception as e:
            print(f"Error executing query: {str(e)}")
            if isinstance(db_pool, Session):
                db_pool.rollback()  # Ensure rollback in case of error
            return None, False


        
    @classmethod
    async def update_attr(self, dbClassNam, data, db_pool):
        try:
            table = None
            if dbClassNam == TableNameEnum.ORGANIZER:
                organizer_name = data.get("organizer_name")
                if not organizer_name:
                    return False
                org_statement = select(ORGANIZER).filter(ORGANIZER.organizer_name == organizer_name)
                table = db_pool.exec(org_statement).first()

            elif dbClassNam == TableNameEnum.Event:
                organizer_name = data.get("organizer_name")
                if not organizer_name:
                    return False
                org_statement = select(Event).filter(Event.organizer_name == organizer_name)
                table = db_pool.exec(org_statement).first()

            elif dbClassNam == TableNameEnum.RSVP:
                event_id = data.get("event_id")
                username = data.get("username")
                if not event_id or not username:
                    return False
                statement = select(RSVP).filter(RSVP.event_id == event_id, RSVP.username == username)
                table = db_pool.exec(statement).first()
                print(f"Updated RSVP: {table}") 

            if not table:
                return False 
            
            print(f"Updating RSVP: {table}") 

            for key, value in data.items():
                setattr(table, key, value)
            

            db_pool.commit()
            return table  

        except Exception as e:
            db_pool.rollback()
            traceback.print_exc()
            return False




    @staticmethod
    async def get_organizer(data: int | str, db_pool: Session):
        try:
            if type(data) == int:
                statement = (select(ORGANIZER.organizer_name, ORGANIZER.name,ORGANIZER.email, ORGANIZER.password, ORGANIZER.contact).where(ORGANIZER.id == data))
            else:
                if "@" in data:
                    statement = (select(ORGANIZER.organizer_name, ORGANIZER.name, ORGANIZER.email, ORGANIZER.password).where(ORGANIZER.email == data))
                else:
                    statement = select(ORGANIZER).where(ORGANIZER.organizer_name == data)
            org = db_pool.exec(statement).first()
            return org
        
        except Exception as e:
            db_pool.rollback()
            traceback.print_exc()
            return None

    @classmethod
    async def getOrganizerSession(self, db_pool, session_token):
            try:
                statement = select(ORGANIZER_SESSION).where(ORGANIZER_SESSION.pk == session_token)
                org_session = db_pool.exec(statement).first()
                if org_session:
                    return org_session
            except:
                return None

    @classmethod
    async def delete(self, data, db_pool):
        try:
            db_pool.delete(data)
            db_pool.commit()
            return True
        except:
            db_pool.rollback()
            traceback.print_exc()
            return False


def authentication_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            db_pool: Optional[Session] = kwargs.get("db_pool", None)
            request: Request = kwargs.get("request")

            if not request:
                return send_json_response(message="Authentication token not provided.", status=status.HTTP_403_FORBIDDEN, body={})
            session_token: Optional[str] = request.cookies.get(variables.COOKIE_KEY, None)
            if not session_token:
                return send_json_response(message="Authentication token not provided.", status=status.HTTP_403_FORBIDDEN, body={})

            if db_pool:
                org_session = await EVENT_DB.getOrganizerSession(db_pool, session_token)
                if not org_session:
                    return send_json_response(message="Session expired/invalid, please login again", status=status.HTTP_403_FORBIDDEN, body={})

                if int(time.time()) > org_session.expired_at:
                    statement = delete(ORGANIZER_SESSION).where(ORGANIZER_SESSION.pk == session_token)
                    db_pool.exec(statement)
                    db_pool.commit()
                    return send_json_response(message="Session expired/invalid, please login again", status=status.HTTP_403_FORBIDDEN, body={})
                kwargs["request"].state.org = org_session 
        except Exception as e:
            print("Exception caught at authentication wrapper: ", str(e))
            if db_pool:
                db_pool.rollback()  
            traceback.print_exc()
            return send_json_response(message="Authentication token not provided.", status=status.HTTP_403_FORBIDDEN, body={})
        return await func(*args, **kwargs) 
    return wrapper