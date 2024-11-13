from datetime import timedelta, datetime, timezone
from typing import Annotated 

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from sqlalchemy.orm import Session
from starlette import status 

from passlib.context import CryptContext
from jose import jwt, JWTError

from database import sessionLocal 
from models import User
from schemas import CreateUserRequest, Token, EmailSchema
from routers import email_verification 
from utils import is_secure_password

import os

from dotenv import load_dotenv


load_dotenv()


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM =os.getenv("ALGORITHM")

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


def get_db():
    db = sessionLocal()
    
    try:
        yield db
    finally:
        db.close() 

db_dependency = Annotated[Session, Depends(get_db)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    
    # Check is user with this username already exists
    user_username = db.query(User).filter(User.username == create_user_request.username).first()
    user_email = db.query(User).filter(User.email == create_user_request.email).first()
    if user_username:
        raise HTTPException(status_code=400, detail="User with this username already exists")
    elif user_email:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Check password security level
    password_status, password_detail = is_secure_password(create_user_request.password)
    if not password_status:
        raise HTTPException(status_code=400, detail=password_detail)

    # Create user
    create_user_model = User(
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        email=create_user_request.email
    )

    # Verification email sending
    token = email_verification.token(create_user_request.email)
    email_verification_endpoint = f'http://localhost:8000/auth/confirm-email/{token}/'
    mail_body = {
        'email':create_user_request.email,
        'project_name': "eventify.az",
        'url': email_verification_endpoint
    }

    mail_status = await email_verification.send_email_async(subject="Email Verification: Registration Confirmation",
        email_to=create_user_request.email, body=mail_body, template='email_verification.html') 

    if mail_status:
        db.add(create_user_model)
        db.commit()
        return {
            "message":"mail for Email Verification has been sent, kindly check your inbox.",
            "status": status.HTTP_201_CREATED
        }
    else:
        return {
            "message":"mail for Email Verification failled to send, kindly reach out to the server guy.",
            "status": status.HTTP_503_SERVICE_UNAVAILABLE
        }

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: db_dependency):
    
    # Check if user exists
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user or not user.is_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')
    
    token = create_access_token(user.username, user.id, timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}


def authenticate_user(username: str, password: str, db):
    
    user = db.query(User).filter(User.username == username).first()
    # Check if user with such username exists
    if not user:
        return False
    # Check if input password matches user's actual password
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    
    return user


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})

    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends (oauth2_bearer)],
                           db: db_dependency
                           ):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get ('sub')
        user_id: int = payload.get('id')

        # Check if payload is valid
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate user.')
        
        user = db.query(User).filter(User.id == user_id).first()
        return {"username": username, 
                "id": user_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_organizer": user.is_organizer,
                "is_admin": user.is_admin
                }
    
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user.')


@router.get("/verify-token", status_code=status.HTTP_200_OK)
async def verify_token(token: Annotated[str, Depends(oauth2_bearer)], db: db_dependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")

        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        return {"is_authenticated": True}

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")


# Email verification

@router.get('/confirm-email/{token}', status_code=status.HTTP_200_OK)
async def user_verification(token:str, db: db_dependency):

    token_data = email_verification.verify_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail= "Token for Email Verification has expired."
        )
    
    user = db.query(User).filter(User.email == token_data['email']).first()

    if not user:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= f"User with email {user.email} does not exist"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code= status.HTTP_409_CONFLICT,
            detail= f"User with email {user.email}, is already verified"
        )
    
    user.is_verified = True
    db.commit()
    db.refresh(user)
    
    return {
            'message':'Email Verification Successful',
            'status':status.HTTP_202_ACCEPTED
        }


@router.post('/resend-verification', status_code=status.HTTP_201_CREATED)
async def resend_email_verification(email_data:EmailSchema, db: db_dependency):
 
    user_check = db.query(User).filter(User.email == email_data.email).first()
    if not user_check:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
        detail= "User information does not exist")
        
    if user_check.is_verified:
        raise HTTPException(
            status_code= status.HTTP_409_CONFLICT,
            detail= f"User with email {user_check.email}, is already verified"
        )    

    token = email_verification.token(email_data.email)
    email_verification_endpoint = f'http://localhost:8000/auth/confirm-email/{token}/'
    mail_body = { 
        'email': user_check.email,
        'project_name': "eventify.az",
        'url': email_verification_endpoint
    }

    mail_status = await email_verification.send_email_async(subject="Email Verification: Registration Confirmation",
    email_to=str(user_check.email), body=mail_body, template='email_verification.html')

    if mail_status:
        return {
            "message":"mail for Email Verification has been sent, kindly check your inbox.",
            "status": status.HTTP_201_CREATED
        }
    else:
        return {
            "message":"mail for Email Verification failled to send, kindly reach out to the server guy.",
            "status": status.HTTP_503_SERVICE_UNAVAILABLE
        }


# Get user data
@router.post("/user")
async def user_data(user: Annotated[get_current_user, Depends()]):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return user   
