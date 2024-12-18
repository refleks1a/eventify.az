from typing import Annotated

import re

from .utils import event_types, is_past_date, time_regex, link_regex, get_redis

from fastapi import APIRouter, Depends, Response

import ast

from redis import Redis

from sqlalchemy.sql.expression import text
from sqlalchemy import or_
from sqlalchemy.orm import Session

from starlette import status 

from database import sessionLocal 

from dotenv import load_dotenv

from models import Event, EventComment, EventLike, Venue, User
from schemas import (EventLikeCreate, EventCreate,
        EventCommentCreate, EventCommentInfo, EventCommentDelete)

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
user_dependency = Annotated[dict, Depends(get_current_user)]
redis_dependency = Annotated[Redis, Depends(get_redis)]


# Events

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate, db: db_dependency,
        current_user: user_dependency):
    
    # Check if user is organizer or not
    if not current_user["is_organizer"]:
        return Response(status_code=status.HTTP_403_FORBIDDEN, 
            content="Only organizers can create events")

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


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_events(db: db_dependency, redis: redis_dependency):
    
    try:
        cached_events = redis.get("events").decode('utf-8')[1: -1]
        split_cached_events = re.split(r"(?<=\}),\s*(?=\{)", cached_events)
        if cached_events:
            split_cached_events = split_cached_events 
            events = [ast.literal_eval(event) for event in split_cached_events]
        else:
            events = db.query(Event).order_by(text("num_likes")).all()
            redis.set("events", str([{
                "id": event.__dict__.get("id"),
                "date": event.__dict__.get("date"),
                "organizer_id": event.__dict__.get("organizer_id"),
                "poster_image_link": event.__dict__.get("poster_image_link"),
                "num_likes": event.__dict__.get("num_likes"),
                "start": event.__dict__.get("start"),
                "finish":event.__dict__.get("finish"),
                "title": event.__dict__.get("title"),
                "description": event.__dict__.get("description"),
                "venue_id": event.__dict__.get("venue_id"),
                "event_type": event.__dict__.get("event_type"),
                "created_at": event.__dict__.get("created_at"),
                "lat": event.__dict__.get("lat"),
                "lng": event.__dict__.get("lng"),
            } for event in events]))
    except AttributeError:
        events = db.query(Event).order_by(text("num_likes")).all()
        redis.set("events", str([{
                "id": event.__dict__.get("id"),
                "date": event.__dict__.get("date").strftime("%Y-%m-%d %H:%M:%S"),
                "organizer_id": event.__dict__.get("organizer_id"),
                "poster_image_link": event.__dict__.get("poster_image_link"),
                "num_likes": event.__dict__.get("num_likes"),
                "start": event.__dict__.get("start").strftime("%H:%M:%S"),
                "finish":event.__dict__.get("finish").strftime("%H:%M:%S"),
                "title": event.__dict__.get("title"),
                "description": event.__dict__.get("description"),
                "venue_id": event.__dict__.get("venue_id"),
                "event_type": event.__dict__.get("event_type"),
                "created_at":event.__dict__.get("created_at").strftime("%Y-%m-%d %H:%M:%S"),
                "lat": event.__dict__.get("lat"),
                "lng": event.__dict__.get("lng"),
            } for event in events]))
        
    return events

@router.get("/favorites", status_code=status.HTTP_200_OK)
async def get_favorite_events(db: db_dependency, current_user: user_dependency):
    
    likes = db.query(EventLike).filter(EventLike.owner_id == current_user["id"]).all()
    venues = db.query(Venue).all()
    events = []

    for like in likes:
        event = db.query(Event).filter(Event.id == like.event).first()
        # If event is not Null append it to events list
        if event:
            for venue in venues:
                if venue.id == event.venue_id:
                    break
            events.append({
                "event": event,
                "location": {
                    "lat": venue.lat,
                    "lng": venue.lng
                }
            })

    return events


@router.get("/{event_id}", status_code=status.HTTP_200_OK)
async def get_event(event_id: int, db: db_dependency):

    # Check event id validity
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return Response(status_code=status.HTTP_404_NOT_FOUND,
            content="Invalid event id")
    venue = db.query(Venue).filter(Venue.id == event.venue_id).first()
    
    return {
        "event": event,
        "location": {
            "lat": venue.lat,
            "lng": venue.lng
        }
    }

# Likes

@router.post("/like", status_code=status.HTTP_201_CREATED)
async def create_event_like(event_like: EventLikeCreate, db: db_dependency,
        current_user: user_dependency):
    
    # Check event id validity
    event = db.query(Event).filter(Event.id == event_like.event).first()
    if not event:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, 
            content="Invalid event id")

    # Check whether like exists or not
    check_db_event_like = db.query(EventLike).filter(EventLike.event == event_like.event,
        EventLike.owner_id == current_user["id"]).first()
    if check_db_event_like:
        return Response(status_code=status.HTTP_400_BAD_REQUEST,
            content="Like already exists")
    
    db_event_like = EventLike(**event_like.model_dump(), owner_id=current_user["id"])

    db.add(db_event_like)
    event.num_likes += 1
    db.commit() 
    db.refresh(db_event_like)

    return Response(status_code=status.HTTP_201_CREATED) 
    

@router.delete("/like", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_like(event_like: EventLikeCreate, db: db_dependency,
        current_user: user_dependency):
    
    # Check event id validity
    event = db.query(Event).filter(Event.id == event_like.event).first()
    if not event:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, 
            content="Invalid event id")

    # Check whether like exists or not
    check_db_event_like = db.query(EventLike).filter(EventLike.event == event_like.event,
        EventLike.owner_id == current_user["id"])
    if not check_db_event_like:
        return Response(status_code=status.HTTP_400_BAD_REQUEST,
            content="Like doesn't exist")
    
    check_db_event_like.delete(synchronize_session=False)
    event.num_likes -= 1 

    if event.num_likes < 0:
        event.num_likes = 0

    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Comments

@router.post("/comment", status_code=status.HTTP_201_CREATED)
def create_event_comment(event_comment: EventCommentCreate, db: db_dependency,
        current_user: user_dependency):

    # Check event id validity
    if not db.query(Event).filter(Event.id == event_comment.event).all():
        return Response(status_code=status.HTTP_400_BAD_REQUEST, 
            content="Invalid event id")

    new_comment = EventComment(**event_comment.model_dump(), owner_id=current_user["id"])
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return Response(status_code=status.HTTP_201_CREATED)


@router.get("/{event_id}/comment", status_code=status.HTTP_200_OK)
def get_event_comments(event_id: int, db: db_dependency):

    comments = db.query(EventComment).filter(EventComment.event == event_id).order_by(text("-created_at")).all()

    return comments


@router.get("/comment/{comment_id}", status_code=status.HTTP_200_OK)
def get_comment(comment_id: int, db: db_dependency):

    # Check if comment exists
    comment = db.query(EventComment).filter(EventComment.id == comment_id).first()
    if not comment:
        return Response(status_code=status.HTTP_404_NOT_FOUND,
                content=f"Comment with id: {comment_id} was not found")

    return comment


@router.delete("/comment", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_comment(event_comment: EventCommentDelete, db: db_dependency,
        current_user: user_dependency):
    
    # Check if comment exists or not
    check_db_event_comment = db.query(EventComment).filter(EventComment.id == event_comment.id,
        EventComment.owner_id == current_user["id"])
    if not check_db_event_comment:
        return Response(status_code=status.HTTP_400_BAD_REQUEST,
            content="Comment doesn't exist")
    
    check_db_event_comment.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Search events

@router.get("/search/{query}", status_code=status.HTTP_200_OK)
async def search_events(query: str, db: db_dependency):

    events = db.query(Event).filter(or_(
            Event.title.ilike(f"%{query[:127]}%"),
            Event.description.ilike(f"%{query[:127]}%"))
        ).limit(10).all()
    venues = db.query(Venue).all()

    events_data = []

    for event in events:
        for venue in venues:
            if venue.id == event.venue_id:
                break
        
        events_data.append({
            "event": event,
            "location": {
                "lat": venue.lat,
                "lng": venue.lng
            }
        })
    

    return events_data
