from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from redis import Redis
import os
from dotenv import load_dotenv

from routers import auth, venues, events, social_auth, chat_rooms
from aws import s3


# Create FastAPI application
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

# Connect to Redis on start up 
@app.on_event("startup")
async def startup_event():
    redis_url = os.getenv("REDIS_URL")
    app.state.redis = Redis.from_url(redis_url)


# Disconnect from Redis on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    app.state.redis.close()


app.include_router(auth.router)
app.include_router(venues.router)
app.include_router(events.router)
app.include_router(social_auth.router)
app.include_router(chat_rooms.router)
app.include_router(s3.router)
