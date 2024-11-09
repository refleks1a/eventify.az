from fastapi import APIRouter
from fastapi_sso.sso.google import GoogleSSO
from fastapi_sso.sso.facebook import FacebookSSO

from starlette import status
from starlette.requests import Request

from dotenv import load_dotenv
import os


load_dotenv()

router = APIRouter(
    prefix="/social_auth",
    tags=["social_auth"]
)

# Google sign in/up

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_SECRET_ID = os.getenv("GOOGLE_SECRET_ID")

google_sso = GoogleSSO(GOOGLE_CLIENT_ID, GOOGLE_SECRET_ID, "http://127.0.0.1:8000/social_auth/google/callback")

@router.get("/google/login")
async def google_login():
    async with google_sso:
        return await google_sso.get_login_redirect()

@router.get("/google/callback", status_code=status.HTTP_200_OK)
async def google_callback(request: Request):
    async with google_sso:
        user = await google_sso.verify_and_process(request)

        user_info = {
            "id": getattr(user, "id", None),
            "email": getattr(user, "email", None),
            "first_name": getattr(user, "first_name", None),
            "last_name": getattr(user, "last_name", None),
            "display_name": getattr(user, "display_name", None),
            "picture": getattr(user, "picture", None),
            "provider": "google"
        }
    if user:
        return {
            "response": "Authorization successful",
            "data": user_info
        }
    return {"response" : "Authorization failed"} 
