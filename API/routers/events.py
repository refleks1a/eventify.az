from typing import Annotated 

import re

from .utils import event_types, is_past_date, time_regex, link_regex

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.sql.expression import text

from sqlalchemy.orm import Session
from starlette import status 

from database import sessionLocal 

from dotenv import load_dotenv

from models import Event, EventComment, EventLike, Venue, User
from schemas import (UserInfo, EventLikeCreate, EventCreate,
        EventCommentCreate, EventCommentInfo, EventCommentBase, EventCommentDelete)

from .auth import get_current_user


load_dotenv()

router = APIRouter(
    prefix="/events",
    tags=["events"]
)

def get_db():
    db = sessionLocal()
    
    try:
        yield db
    finally:
        db.close() 

db_dependency = Annotated[Session, Depends(get_db)]


# Events

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate, db: db_dependency):
    
    # Check venue_id validity
    if not db.query(Venue).filter(Venue.id == event.venue_id).all():
        return Response(status_code=status.HTTP_400_BAD_REQUEST, 
            content="Invalid venue id")
    
    # Check organizer_id validity
    if not db.query(User).filter(User.id == event.organizer_id).all():
        return Response(status_code=status.HTTP_400_BAD_REQUEST, 
            content="Invalid organizer id")
    
    # Check event_type validity
    if event.event_type not in event_types:
        return Response(status_code=status.HTTP_400_BAD_REQUEST,
            content="Invalid event type")
    
    # Check date validity
    if is_past_date(str(event.date)[:19]):
        return Response(status_code=status.HTTP_400_BAD_REQUEST,
            content="Event date cannot be in the past")

    # Check star/finish time validity
    if (event.start > event.finish) or (not bool(re.match(time_regex, str(event.start)[:8]))) or (
        not bool(re.match(time_regex, str(event.finish)[:8]))):
        return Response(status_code=status.HTTP_400_BAD_REQUEST, 
            content="Invalid start/finish time of event")

    # Check poster_image_link validity
    if not bool(re.match(link_regex, str(event.poster_image_link))):
        return Response(status_code=status.HTTP_400_BAD_REQUEST, 
            content="Invalid link")
    
    db_event = Event(**event.model_dump())
    db.add(db_event)
    db.commit() 
    
    return Response(status_code=status.HTTP_201_CREATED)


@router.get("/all", status_code=status.HTTP_200_OK)
async def get_all_events(db: db_dependency):
    
    events = db.query(Event).order_by(text("num_likes")).all()
    
    return events

@router.get("/favorites", status_code=status.HTTP_200_OK)
async def get_favorite_events(db: db_dependency, 
        current_user: UserInfo = Depends(get_current_user)):
    likes = db.query(EventLike).filter(EventLike.owner_id == current_user.id).all()
    events = []

    for like in likes:
        event = db.query(Event).filter(Event.id == like.event).first()
        # If event is not Null append it to events list
        if event:
            events.append(event)

    return events


@router.get("/{event_id}", status_code=status.HTTP_200_OK)
async def get_event(event_id: int, db: db_dependency):

    # Check event id validity
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return Response(status_code=status.HTTP_404_NOT_FOUND,
            content="Invalid event id")
    
    return event

# Likes

@router.post("/like", status_code=status.HTTP_201_CREATED)
async def create_event_like(event_like: EventLikeCreate, db: db_dependency,
        current_user: UserInfo = Depends(get_current_user)):
    
    # Check event id validity
    if not db.query(Event).filter(Event.id == event_like.event).all():
        return Response(status_code=status.HTTP_400_BAD_REQUEST, 
            content="Invalid event id")

    # Check whether like exists or not
    check_db_event_like = db.query(EventLike).filter(EventLike.event == event_like.event,
        EventLike.owner_id == current_user.id).first()
    if check_db_event_like:
        return Response(status_code=status.HTTP_400_BAD_REQUEST,
            content="Like already exists")
    
    event = db.query(Event).filter(Event.id == event_like.event).first()
    event.num_likes += 1

    db_event_like = EventLike(**event_like.model_dump(), owner_id=current_user.id)

    db.add(db_event_like)
    db.commit() 
    db.refresh(db_event_like)

    return Response(status_code=status.HTTP_201_CREATED) 
    

@router.delete("/like/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_like(event_like: EventLikeCreate, db: db_dependency,
        current_user: UserInfo = Depends(get_current_user)):
    
    # Check event id validity
    if not db.query(Event).filter(Event.id == event_like.event).all():
        return Response(status_code=status.HTTP_400_BAD_REQUEST, 
            content="Invalid event id")

    # Check whether like exists or not
    check_db_event_like = db.query(EventLike).filter(EventLike.event == event_like.event,
        EventLike.owner_id == current_user.id)
    if not check_db_event_like:
        return Response(status_code=status.HTTP_400_BAD_REQUEST,
            content="Like doesn't exist")

    event = db.query(Event).filter(Event.id == event_like.event).first()
    check_db_event_like.delete(synchronize_session=False)
    event.num_likes -= 1 

    if event.num_likes < 0:
        event.num_likes = 0

    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Comments

@router.post("/comment", status_code=status.HTTP_201_CREATED, response_model= EventCommentInfo)
def create_event_comment(event_comment: EventCommentCreate, db: Session = Depends(get_db),
        current_user: UserInfo = Depends(get_current_user)):

    # Check event id validity
    if not db.query(Event).filter(Event.id == event_comment.event).all():
        return Response(status_code=status.HTTP_400_BAD_REQUEST, 
            content="Invalid event id")

    new_comment = EventComment(**event_comment.model_dump(), owner_id=current_user.id)
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return Response(status_code=status.HTTP_201_CREATED)


@router.get("/{event_id}/comment", status_code=status.HTTP_200_OK)
def get_event_comments(event_id: int, db: Session = Depends(get_db)):

    comments = db.query(EventComment).filter(EventComment.event == event_id).order_by(text("-created_at")).all()

    return comments


@router.get("/comment/{comment_id}", status_code=status.HTTP_200_OK)
def get_comment(comment_id: int, db: Session = Depends(get_db)):

    comment = db.query(EventComment).filter(EventComment.id == comment_id).first()

    if not comment:
        return Response(status_code=status.HTTP_404_NOT_FOUND,
                content=f"Comment with id: {comment_id} was not found")

    return comment


@router.delete("/comment/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_comment(event_comment: EventCommentDelete, db: db_dependency,
        current_user: UserInfo = Depends(get_current_user)):
    
    # Check whether comment exists or not
    check_db_event_comment = db.query(EventComment).filter(EventComment.id == event_comment.id,
        EventComment.owner_id == current_user.id)
    if not check_db_event_comment:
        return Response(status_code=status.HTTP_400_BAD_REQUEST,
            content="Comment doesn't exist")
    
    check_db_event_comment.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
