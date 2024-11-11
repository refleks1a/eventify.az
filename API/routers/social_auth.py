from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, Response
from fastapi_sso.sso.google import GoogleSSO
# from fastapi_sso.sso.facebook import FacebookSSO

from starlette import status
from starlette.requests import Request

from passlib.context import CryptContext

from sqlalchemy.orm import Session

from dotenv import load_dotenv
import os
from typing import Annotated 
from datetime import timedelta

from models import User
from database import sessionLocal 
from .auth import authenticate_user, create_access_token
from .utils import remove_domain


def get_db():
    db = sessionLocal()
    
    try:
        yield db
    finally:
        db.close() 

db_dependency = Annotated[Session, Depends(get_db)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

load_dotenv()

router = APIRouter(
    prefix="/social_auth",
    tags=["social_auth"]
)

# Google sign in/up

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_SECRET_ID = os.getenv("GOOGLE_SECRET_ID")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

google_sso = GoogleSSO(GOOGLE_CLIENT_ID, GOOGLE_SECRET_ID, GOOGLE_REDIRECT_URI)


@router.get("/google/login")
async def google_login():
    async with google_sso:
        return await google_sso.get_login_redirect()


@router.get("/google/callback", status_code=status.HTTP_200_OK)
async def google_callback(request: Request, db: db_dependency):
    async with google_sso:
        response = await google_sso.verify_and_process(request)

        user_data = {
            "id": getattr(response, "id", None),
            "email": getattr(response, "email", None),
            "first_name": getattr(response, "first_name", None),
            "last_name": getattr(response, "last_name", None),
            "display_name": getattr(response, "display_name", None),
            "picture": getattr(response, "picture", None),
            "provider": "google"
        }

        if user_data["display_name"]:
            user_data["username"] = user_data["display_name"]
        else:
            user_data["username"] = remove_domain(user_data["email"])

    if response:
        user = db.query(User).filter(User.email == user_data["email"]).first()
        # Sign in
        if user:
            if user.provider == "google":
                authenticate_user(user.username, f"{user.social_id}{user.provider}", db)
                token = create_access_token(user.username, user.id, timedelta(minutes=20))

                return {"access_token": token, "token_type": "bearer"}
                # return RedirectResponse(url="http://localhost:3000/CLIENT")
            else:
                return {"response": "Invalid provider", "status": status.HTTP_403_FORBIDDEN}
        # Sign up
        else:
            # Check is user with this username already exists
            existing_user = db.query(User).filter(
                (User.username == user_data["username"]) | (User.email == user_data["email"])
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Account with this information already exists")

            # Create user
            create_user_model = User(
                username=user_data["username"],
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                hashed_password=bcrypt_context.hash(str(user_data["id"]) + str(user_data["provider"])),
                social_id=user_data["id"],
                provider=user_data["provider"],
                is_verified=True
            )
            # Save user to database
            db.add(create_user_model)
            db.commit()

            return {
                "message":"Account was successfully created",
                "status": status.HTTP_201_CREATED
            }

    return {"response" : "Authorization failed", "status": status.HTTP_401_UNAUTHORIZED} 
