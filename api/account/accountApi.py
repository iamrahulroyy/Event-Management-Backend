from fastapi import APIRouter, Depends, Request
from sqlmodel import Session
from DB.database import DataBasePool, authentication_required
from api.account.account import user
from extra.datamodel import Login_user, Register_user

accountRouter = APIRouter(prefix="/organizer", tags=["Account Route"])

account = user()

@accountRouter.post("/signup")
async def organizer_signup(request: Request, data: Register_user, db_pool:Session = Depends(DataBasePool.get_pool)):
    return await account.organizer_signup(request, data, db_pool)

@accountRouter.post("/login")
async def organizer_login(request: Request, data: Login_user , db_pool:Session = Depends(DataBasePool.get_pool)):
    return await account.organizer_login(request, data, db_pool)

@accountRouter.post("/logout")
@authentication_required
async def organizer_logout(request: Request,db_pool=Depends(DataBasePool.get_pool)):
    return await account.organizer_logout(request, db_pool)

@accountRouter.get("/auth", name="Check Logged Status")
@authentication_required
async def check_auth(request: Request,db_pool:Session = Depends(DataBasePool.get_pool)):
    return await account.check_auth(request, db_pool)