from sqlalchemy import Boolean, Column, Integer, String

from blog.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(63), unique=True)


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(123))
    content = Column(String(255))
    user_id = Column(Integer)
