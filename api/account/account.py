
import time
import traceback
import uuid
from fastapi import Request,status
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session
from DB.database import EVENT_DB
from DB.models import ORGANIZER_METAReasonEnum, TableNameEnum
from api.account.helper import security
from api.error.error import error_handler
from extra import variables
from extra.datamodel import Login_user, Register_user
from extra.helper import get_fastApi_req_data, send_json_response


db = EVENT_DB()

class user:
    def __init__(self):
        pass

    @staticmethod
    async def organizer_signup(request:Request , data:Register_user, db_pool:Session):

        organizer_name = data.organizer_name.strip()
        email = data.email.lower()
        contact = int(''.join(filter(str.isdigit, str(data.contact)))[:10])
        name = data.name.strip()

        password = security().hash_password(data.password)

        if len(organizer_name) == 0:
            return error_handler("Invalid organizer name", 403)
        
        if not organizer_name.isalnum():
            return error_handler("Only alphanumeric characters are allowed", 403)
        try:
            if await db.get_organizer(organizer_name, db_pool) is not None:
                return send_json_response(message="Username not available.",status=status.HTTP_403_FORBIDDEN,body={},)
            
            if await db.get_organizer(organizer_name, db_pool):
                return send_json_response(message="Email already registered, Please try again.",status=status.HTTP_403_FORBIDDEN,body={},)
            
            if await db.get_organizer(organizer_name, db_pool):
                return send_json_response(message="Phone number already registered, Please try again.",status=status.HTTP_403_FORBIDDEN,body={},)
            
            apiData = await get_fastApi_req_data(request)

            organizer_data = {"organizer_name":organizer_name, "email":email, "password": password, "name": name, "contact":contact } 

            inserted_user, ok = await db.insert(TableNameEnum.ORGANIZER, organizer_data, db_pool)

            if not ok or not inserted_user:
                return send_json_response(message="Could not create organizer account, please try again",status=status.HTTP_500_INTERNAL_SERVER_ERROR,body={},)
            
            serialized_inserted_user = jsonable_encoder(inserted_user)
            sensitive_fields = ["password","updated_at"]
            for field in sensitive_fields:
                serialized_inserted_user.pop(field, None)
        
            organizer_META_DATA = {
                "organizer_name": organizer_name,
                "reason": ORGANIZER_METAReasonEnum.SIGNUP,
                "browser": apiData.browser,
                "os": apiData.os,
            }
            inserted_user_metadata, _ = await db.insert(TableNameEnum.ORGANIZER_META, organizer_META_DATA, db_pool)
            serialized_inserted_user.pop("id", None)
            return send_json_response(message="Organizer account created successfully!",status=status.HTTP_201_CREATED,body=serialized_inserted_user,)
        
        except Exception as e:
            print("Exception caught at organizer signup: ", str(e))
            traceback.print_exc()
            return send_json_response(message="Error during organizer signup process, please try again later!",status=status.HTTP_500_INTERNAL_SERVER_ERROR,body={},)
        
    @staticmethod
    async def organizer_login(request:Request,data: Login_user,db_pool):
        try:
            apiData = await get_fastApi_req_data(request)
            if not data.data:
                return send_json_response(message="Invalid credentials",status=status.HTTP_401_UNAUTHORIZED,body={},)
            
            org_data = data.data.lower()
            org = await db.get_organizer(org_data, db_pool)
            if not org:
                return send_json_response(message="Organizer account not found",status=status.HTTP_401_UNAUTHORIZED,body={},)
            
            serialized_inserted_org = jsonable_encoder(org)

            if not security().verify_password(org.password, data.password):
                return send_json_response(message="Invalid credentials",status=status.HTTP_401_UNAUTHORIZED,body={},)

            token = str(uuid.uuid4())
            if data.keepLogin:
                max_age = 3600 * 24 * 30
            else:
                max_age = 3600 * 90
            expiry = int(time.time() + max_age)

            session_data = {"pk": token,"organizer_name":org.organizer_name, "ip": apiData.ip, "browser": apiData.browser,
                            "os": apiData.os, "created_at": int(time.time()), "expired_at": expiry}
            session, ok = await db.insert(dbclassnam=TableNameEnum.ORGANIZER_SESSION, data=session_data, db_pool=db_pool)

            organizer_META_DATA = {"organizer_name": org.organizer_name, "reason" : ORGANIZER_METAReasonEnum.LOGIN, "os": apiData.os}
            await db.insert(dbclassnam=TableNameEnum.ORGANIZER_META,  data= organizer_META_DATA, db_pool=db_pool)

            response = send_json_response(message="Organizer logged in successfully",status=status.HTTP_200_OK,body=[],)

            response.set_cookie(key=variables.COOKIE_KEY, value=token, max_age=max_age, httponly=True, secure=True, samesite="None")
            return response
        except Exception as e:
            print("Exception caught at organizer Signin: ", str(e))
            traceback.print_exc()
            return send_json_response(message="Login Failed",status=status.HTTP_401_UNAUTHORIZED,body={},)
        
    @staticmethod    
    async def organizer_logout(request, db_pool):
        try:
            await db.delete(request.state.org, db_pool)
            response = send_json_response(message="logged out successfully",status=status.HTTP_200_OK,body={})
            response.delete_cookie(key=variables.COOKIE_KEY)
            return response
        except Exception as e:
            traceback.print_exc()
            return send_json_response(message="Logout Failed",status=status.HTTP_401_UNAUTHORIZED,body={})
        
    @staticmethod
    async def check_auth(request: Request, db_pool: Session):
        try:
            cur_org = await db.get_organizer(request.state.org.organizer_name, db_pool=db_pool)
            if cur_org:
                return send_json_response(message="Session valid.", status=status.HTTP_200_OK,body={"email": cur_org.email, "organizer name": cur_org.organizer_name, "contact number": cur_org.contact })
            else: 
                return send_json_response(message= "Session invalid", status= status.HTTP_400_BAD_REQUEST, body={})
        except Exception as e:
            print("Exception caught at checking user logged state: ", str(e))
            return send_json_response(message="Failed to check user auth status, please try again later!", status=status.HTTP_500_INTERNAL_SERVER_ERROR, body={})







        