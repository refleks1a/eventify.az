from typing import Annotated 

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.sql.expression import text

from sqlalchemy.orm import Session
from starlette import status 

from database import sessionLocal 

from dotenv import load_dotenv

from models import Venue, VenueComment, VenueLike
from schemas import (UserInfo, VenueLikeCreate, VenueCreate,
        VenueCommentCreate, VenueCommentInfo, VenueCommentBase)

from .auth import get_current_user


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


# Venues

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_venue(venue: VenueCreate, db: db_dependency):
    # Check lat/lng validity
    # if not re.match(latitude_regex, event.lat) or not re.match(longitude_regex, event.lng):
    #     return Response(status_code=status.HTTP_400_BAD_REQUEST, 
    #         content="Unprocessable latitude/longitude entry") 
    
    # # Check location validity
    # country, city = get_country_from_coordinates(event.lat, event.lng)
    # if country != "Azerbaijan":
    #     return Response(status_code=status.HTTP_400_BAD_REQUEST,
    #         content=f"Event location is outside of Azerbaijan")

    db_venue = Venue(**venue.model_dump())

    db.add(db_venue)
    db.commit() 


@router.get("/all", status_code=status.HTTP_200_OK)
async def get_all_venues(db: db_dependency):
    
    venues = db.query(Venue).order_by(text("num_likes")).all()
    
    return venues


@router.get("/{venue_id}", status_code=status.HTTP_200_OK)
async def get_venue(venue_id: int, db: db_dependency):
    venue = db.query(Venue).filter(Venue.id == venue_id).first()

    if not venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return venue

# Likes

@router.post("/like", status_code=status.HTTP_201_CREATED)
async def create_venue_like(venue_like: VenueLikeCreate, db: db_dependency,
        current_user: UserInfo = Depends(get_current_user)):

    check_db_venue_like = db.query(VenueLike).filter(VenueLike.venue == venue_like.venue,
        VenueLike.owner_id == current_user.id).first()

    if not check_db_venue_like:
        venue = db.query(Venue).filter(Venue.id == venue_like.venue).first()
        venue.num_likes += 1

        db_venue_like = VenueLike(**venue_like.model_dump(), owner_id=current_user.id)

    db.add(db_venue_like)
    db.commit() 
    db.refresh(db_venue_like)

    return db_venue_like


@router.delete("/like/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_venue_like(venue_like: VenueLikeCreate, db: db_dependency,
        current_user: UserInfo = Depends(get_current_user)):
    
    check_db_venue_like = db.query(VenueLike).filter(VenueLike.venue == venue_like.venue,
        VenueLike.owner_id == current_user.id)
    
    if check_db_venue_like:
        venue = db.query(Venue).filter(Venue.id == venue_like.venue).first()
        check_db_venue_like.delete(synchronize_session=False)
        venue.num_likes -= 1 

        if venue.num_likes < 0:
            venue.num_likes = 0

    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)




# Comments

@router.post("/comment", status_code=status.HTTP_201_CREATED, response_model= VenueCommentInfo)
def create_venue_comment(venue_comment: VenueCommentCreate, db: Session = Depends(get_db),
        current_user: UserInfo = Depends(get_current_user)):

    new_comment = VenueComment(**venue_comment.model_dump(), owner_id=current_user.id)
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return Response(status_code=status.HTTP_201_CREATED)


@router.get("/{venue_id}/comment", status_code=status.HTTP_200_OK)
def get_venue_comments(venue_id: int, db: Session = Depends(get_db)):

    comments = db.query(VenueComment).filter(VenueComment.venue == venue_id).order_by(text("-created_at")).all()

    return comments


@router.get("/comment/{comment_id}", status_code=status.HTTP_200_OK)
def get_comment(comment_id: int, db: Session = Depends(get_db)):

    comment = db.query(VenueComment).filter(VenueComment.id == comment_id).first()

    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Comment with id: {comment_id} was not found")

    return comment


@router.delete("/comment/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_venue_comment(venue_comment: VenueCommentBase, db: db_dependency,
        current_user: UserInfo = Depends(get_current_user)):

    check_db_venue_comment = db.query(VenueComment).filter(VenueComment.venue == venue_comment.venue,
        VenueComment.owner_id == current_user.id)
    
    if check_db_venue_comment:
        check_db_venue_comment.delete(synchronize_session=False)

    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
