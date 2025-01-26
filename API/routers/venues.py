from typing import Annotated 

import re

from fastapi import APIRouter, Depends, HTTPException, Response

from sqlalchemy.sql.expression import text
from sqlalchemy.orm import Session
from sqlalchemy import or_

from starlette import status

from database import sessionLocal 

from dotenv import load_dotenv

from models import Venue, VenueComment, VenueLike, User
from schemas import (VenueLikeCreate, VenueCreate, VenueCommentDelete,
        VenueCommentCreate, VenueCommentInfo, VenueCommentBase)

from .auth import get_current_user

from .utils import venue_types, latitude_regex, longitude_regex, time_regex


load_dotenv()

router = APIRouter(
    prefix="/venues",
    tags=["venues"]
)

def get_db():
    db = sessionLocal()
    
    try:
        yield db
    finally:
        db.close() 

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# Venues
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_venue(venue: VenueCreate, db: db_dependency, 
        current_user: user_dependency):
    
    # Check venue validity
    if venue.venue_type not in venue_types:
        return Response(status_code=status.HTTP_400_BAD_REQUEST,
            content="Invalid venue type")

    # Check lat/lng validity
    if not re.match(latitude_regex, venue.lat) or not re.match(longitude_regex, venue.lng):
        return Response(status_code=status.HTTP_400_BAD_REQUEST, 
            content="Unprocessable latitude/longitude entry") 
    
    # Check working hours validity
    if (venue.work_hours_open > venue.work_hours_close) or (not bool(re.match(time_regex, str(venue.work_hours_open)[:8]))) or (
        not bool(re.match(time_regex, str(venue.work_hours_close)[:8]))):
        return Response(status_code=status.HTTP_400_BAD_REQUEST, 
            content="Invalid start/finish time of event")

    # Check if user is organizer
    if not current_user["is_organizer"]:
        return Response(status_code=status.HTTP_403_FORBIDDEN, 
            content="Only organizers can create venues")

    db_venue = Venue(**venue.model_dump())

    db.add(db_venue)
    db.commit() 


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_venues(db: db_dependency): # type: ignore
    
    venues = db.query(Venue).order_by(text("num_likes")).all()    
    return venues


@router.get("/{venue_id}", status_code=status.HTTP_200_OK)
async def get_venue(venue_id: int, db: db_dependency):

    # Check if venue exists
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        return Response(status_code=status.HTTP_404_NOT_FOUND,
            content="No event with id {venue_id}")
        
    return venue

# Likes

@router.post("/like", status_code=status.HTTP_201_CREATED)
async def create_venue_like(venue_like: VenueLikeCreate, db: db_dependency,
        current_user: user_dependency):

    # Check venue id validity
    venue = db.query(Venue).filter(Venue.id == venue_like.venue).first()
    if not venue:
        return Response(status_code=status.HTTP_400_BAD_REQUEST,
            content="Invalid venue id")

    # If Venue like exists
    check_db_venue_like = db.query(VenueLike).filter(
        VenueLike.venue == venue_like.venue,
        VenueLike.owner_id == current_user["id"]).first()
    if check_db_venue_like:
        db.delete(check_db_venue_like)
        venue.num_likes -= 1 
        
        if venue.num_likes < 0:
            venue.num_likes = 0
        
        db.commit() 
        return Response(status_code=status.HTTP_204_NO_CONTENT) 
    
    # Create Venue like
    db_venue_like = VenueLike(**venue_like.model_dump(), owner_id=current_user["id"])

    db.add(db_venue_like)
    venue.num_likes += 1
    db.commit() 
    db.refresh(db_venue_like)
    
    return Response(status_code=status.HTTP_201_CREATED)


# Comments

@router.post("/comment", status_code=status.HTTP_201_CREATED, response_model= VenueCommentInfo)
def create_venue_comment(venue_comment: VenueCommentCreate, db: db_dependency,
        current_user: user_dependency):

    # Check venue id validity
    if not db.query(Venue).filter(Venue.id == venue_comment.venue).all():
        return Response(status_code=status.HTTP_400_BAD_REQUEST, 
            content="Invalid venue id")

    new_comment = VenueComment(**venue_comment.model_dump(), owner_id=current_user["id"])
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return Response(status_code=status.HTTP_201_CREATED)


@router.get("/{venue_id}/comment", status_code=status.HTTP_200_OK)
def get_venue_comments(venue_id: int, db: db_dependency, current_user: user_dependency):

    comments = db.query(VenueComment).filter(VenueComment.venue == venue_id).order_by(text("-created_at")).all()

    data = []

    for comment in comments:
        owner = db.query(User).filter(User.id == comment.owner_id).first()
        data.append(
            {
                "comment": comment,
                "owner": {
                    "id": owner.id,
                    "email": owner.email,
                    "username": owner.username,
                    "last_name": owner.last_name,
                    "first_name": owner.first_name,
                },
            }
        )

    # Sort the data by owner.id, putting the current user's comments first
    sorted_data = sorted(data, key=lambda x: x['owner']['id'] != current_user["id"])

    return sorted_data


@router.get("/comment/{comment_id}", status_code=status.HTTP_200_OK)
def get_comment(comment_id: int, db: db_dependency):

    # Check if comment exists
    comment = db.query(VenueComment).filter(VenueComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Comment with id: {comment_id} was not found")

    owner = db.query(User).filter(User.id == comment.owner_id).first()

    return {
        "comment": comment,
        "owner": {
            "id": owner.id,
            "email": owner.email,
            "username": owner.username,
            "last_name": owner.last_name,
            "first_name": owner.first_name,
        },
    }


@router.delete("/comment", status_code=status.HTTP_204_NO_CONTENT)
async def delete_venue_comment(venue_comment: VenueCommentDelete, db: db_dependency,
        current_user: user_dependency):

    # Check if comment exists or not
    check_db_venue_comment = db.query(VenueComment).filter(VenueComment.id == venue_comment.id,
        VenueComment.owner_id == current_user["id"])
    if not check_db_venue_comment:
        return Response(status_code=status.HTTP_400_BAD_REQUEST,
            content="Comment doesn't exists")

    check_db_venue_comment.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Search venues
@router.get("/search/{query}", status_code=status.HTTP_200_OK)
async def search_venues(query: str, db: db_dependency):

    # venues = db.query(Venue).filter(or_(
    #         Venue.name.ilike(f"%{query[:127]}%"),
    #         Venue.description.ilike(f"%{query[:127]}%"))
    #     ).limit(10).all()
    

    venues = db.query(Venue).filter(Venue.name.ilike(f"%{query[:127]}%")).limit(10).all()
    
    return venues
