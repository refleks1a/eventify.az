from typing import Annotated

import re

from .utils import event_types, is_past_date, time_regex, link_regex

from fastapi import APIRouter, Depends, Response

from sqlalchemy.sql.expression import text
from sqlalchemy import or_
from sqlalchemy.orm import Session

from starlette import status 

from database import sessionLocal 

from dotenv import load_dotenv

from models import ChatRoom, Venue
from schemas import ChatRoomCreate

from .auth import get_current_user


load_dotenv()

router = APIRouter(
    prefix="/chat_rooms",
    tags=["chat_rooms"]
)

def get_db():
    db = sessionLocal()
    
    try:
        yield db
    finally:
        db.close() 

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# Create a room
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_room(room: ChatRoomCreate, db: db_dependency,
        current_user: user_dependency):
    
    # Check if user is admin or not
    if not current_user["is_admin"]:
        return Response(status_code=status.HTTP_403_FORBIDDEN, 
            content="Only admins can create chat rooms")

    # Check venue_id validity
    if not db.query(Venue).filter(Venue.id == room.venue_id).all():
        return Response(status_code=status.HTTP_400_BAD_REQUEST, 
            content="Invalid venue id")
    
    # CHeck max_capacity validity
    if 50 < room.max_capacity or room.max_capacity < 0:
        return Response(status_code=status.HTTP_400_BAD_REQUEST,
            content="Invalid value for max_capacity")
    
    # Check current_capacity validity
    if 0 > room.current_capacity or room.current_capacity > room.max_capacity:
        return Response(status_code=status.HTTP_400_BAD_REQUEST,
            content="Invalid value for current_capacity")

    db_room = ChatRoom(**room.model_dump())
    db.add(db_room)
    db.commit() 
    
    return Response(status_code=status.HTTP_201_CREATED)


# Get all rooms
@router.get("", status_code=status.HTTP_200_OK)
async def get_all_rooms(db: db_dependency, current_user: user_dependency):
    
    rooms = db.query(ChatRoom).order_by(text("-current_capacity")).all()
    
    return rooms

# Search a room
