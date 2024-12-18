from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from passlib.context import CryptContext

from sqlalchemy.orm import Session

from dotenv import load_dotenv
import os
from typing import Annotated 
from datetime import timedelta

from schemas import CreateUserGoogle
from models import User
from database import sessionLocal 
from .auth import authenticate_user, create_access_token, get_current_user, create_refresh_token
from .utils import remove_domain


def get_db():
    db = sessionLocal()
    
    try:
        yield db
    finally:
        db.close() 

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

load_dotenv()

router = APIRouter(
    prefix="/social_auth",
    tags=["social_auth"]
)

# Google sign in/up

async def login(user: user_dependency, db: db_dependency):
    if user.provider == "google":
        authenticate_user(user.username, f"{user.social_id}{user.provider}", db)
        token = create_access_token(user.username, user.id, timedelta(minutes=20))
        refresh_token = create_refresh_token(user.username, user.id)
        return {"access_token": token, "refresh_token": refresh_token, "token_type": "bearer"}

    return {"response": "Invalid provider", "status": status.HTTP_403_FORBIDDEN}


@router.post("/google", status_code=status.HTTP_200_OK)
async def google_auth(db: db_dependency, create_user_request: CreateUserGoogle):

    # Define username
    if create_user_request.display_name:
        username = create_user_request.display_name
    else:
        username = remove_domain(create_user_request.email)

    user = db.query(User).filter(User.email == create_user_request.email).first()
    # In case user exists --
    if user:
        return await login(user, db)

    # In case user doesn't exist --
    # Check is user with this username already exists
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == create_user_request.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Account with this information already exists")

    # Create user
    create_user_model = User(
        username=username,
        email=create_user_request.email,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        hashed_password=bcrypt_context.hash(str(create_user_request.id) + str(create_user_request.provider)),
        social_id=create_user_request.id,
        provider=create_user_request.provider,
        is_verified=True
    )
    # Save user to database
    db.add(create_user_model)
    db.commit()

    new_created_user = db.query(User).filter(User.email == create_user_request.email).first()
    # Login user    
    return await login(new_created_user, db)
