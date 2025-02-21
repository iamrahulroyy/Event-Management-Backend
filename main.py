import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from DB.database import DataBasePool 
from api.event.eventApi import router as event_router
from api.account.accountApi import accountRouter as account_router
from api.response.rsvpApi import rsvpRouter as rsvp_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    await DataBasePool.setup()
    yield
    await DataBasePool.teardown()


app = FastAPI(lifespan=lifespan)


app.include_router(account_router)
app.include_router(event_router)
app.include_router(rsvp_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    print("Server is running on localhost:8000")
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
