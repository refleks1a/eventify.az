from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session

from pydantic import BaseModel

from typing import Annotated

import blog.models as models 
from blog.database import engine, sessionLocal


app = FastAPI()
models.Base.metadata.create_all(bind=engine)


class PostBase(BaseModel):

    user_id: int
    title: str
    content: str


class UserBase(BaseModel):

    username: str


def get_db():
    db = sessionLocal()
    
    try:
        yield db
    finally:
        db.close()    


db_dependency = Annotated[Session, Depends(get_db)]


@app.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserBase, db: db_dependency):
    db_user = models.User(**user.model_dump())
   
    db.add(db_user)
    db.commit()


@app.get("/users/{user_id}", status_code=status.HTTP_200_OK)
async def get_user(user_id: int, db: db_dependency):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return user


@app.post("/posts/", status_code=status.HTTP_201_CREATED)
async def create_post(post: PostBase, db: db_dependency):
    db_post = models.Post(**post.model_dump())

    db.add(db_post)
    db.commit()


@app.get("/posts/{post_id}", status_code=status.HTTP_200_OK)
async def get_post(post_id: int, db: db_dependency):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return post


@app.delete("/posts/{post_id}/delete", status_code=status.HTTP_200_OK)
async def delete_post(post_id: int, db: db_dependency):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    db.delete(post)
    db.commit()
