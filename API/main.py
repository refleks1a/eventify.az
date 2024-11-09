from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from typing import Annotated

from models import Base
from database import engine, sessionLocal
from routers import auth, venues, events, social_auth


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

app.include_router(auth.router)
app.include_router(venues.router)
app.include_router(events.router)
app.include_router(social_auth.router)

Base.metadata.create_all(bind=engine)


def get_db():
    db = sessionLocal()
    
    try:
        yield db
    finally:
        db.close()    


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends (auth.get_current_user)]

@app.post("/user", status_code=status.HTTP_200_OK)
async def user(user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return user
