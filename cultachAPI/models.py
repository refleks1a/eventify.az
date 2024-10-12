from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum, ForeignKey, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.ext.declarative import declared_attr

from datetime import time

from fastapi_storages import FileSystemStorage
from fastapi_storages.integrations.sqlalchemy import FileType


from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(63), unique=True)

    first_name = Column(String(63), nullable=False)
    last_name = Column(String(63), nullable=False)
    hashed_password = Column(String(127))

    is_organizer = Column(Boolean, default=False)


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(123))
    content = Column(String(255))
    user_id = Column(Integer)






class Venue(Base):
    __tablename__ = "venues"
    
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(127), nullable=False, unique=True)
    description = Column(String(511), nullable=False)

    venue_type = Column(Enum("museum", "theatre", "library", "cinema",
        "comedy_club","monument","cultural_space", name="venue_type" ))

    lat = Column(String(257), nullable=False)
    lng = Column(String(257), nullable=False)

    num_likes = Column(Integer, server_default = text("0"), nullable = False, default=0)
    comments = relationship("VenueComment", backref = "venue_comments") 

    image_1_link = Column(String(511), nullable=True)
    image_2_link = Column(String(511), nullable=True)
    image_3_link = Column(String(511), nullable=True)
    
    work_hours_open = Column(Time, default=time(10, 0))
    work_hours_close = Column(Time, default=time(18, 0))


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(127), nullable=False)
    description = Column(String(511), nullable=False)

    date = Column(DateTime, nullable=False)

    venue_id = Column(Integer, ForeignKey("venues.id"), nullable = False)
    venue = relationship("Venue")

    organizer_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    organizer = relationship("User")

    event_type = Column(Enum("theatre", "concert", "exhibition", "book_fare",
        "seminar","festival","dance", name="venue_type" ))

    poster_image_link = Column(String(511), nullable=True)
    
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    
    num_likes = Column(Integer, server_default = text("0"), nullable = False)
    comments = relationship("EventComment", backref = "event_comments")        

    start = Column(Time)
    finish = Column(Time)


class Comment:
    @declared_attr
    def id(cls):
        return Column(Integer, primary_key=True, index=True)

    @declared_attr
    def owner_id(cls):
        return Column(Integer, ForeignKey("users.id"), nullable=False)

    @declared_attr
    def owner(cls):
        return relationship("User")

    @declared_attr
    def content(cls):
        return Column(String(255), nullable=False)

    @declared_attr
    def created_at(cls):
        return Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))


class EventComment(Base, Comment):
    __tablename__ = "event_comments"

    event = Column(Integer, ForeignKey("events.id"), nullable=False)


class VenueComment(Base, Comment):
    __tablename__ = "venue_comments"
    
    venue = Column(Integer, ForeignKey("venues.id"), nullable = False)


class Like:
    @declared_attr
    def id(cls):
        return Column(Integer, primary_key=True, index=True)

    @declared_attr
    def owner_id(cls):
        return Column(Integer, ForeignKey("users.id"), nullable=False)

    @declared_attr
    def owner(cls):
        return relationship("User")

    @declared_attr
    def created_at(cls):
        return Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))


class EventLike(Base, Like):
    __tablename__ = "event_likes"

    event = Column(Integer, ForeignKey("events.id"), nullable=False)


class VenueLike(Base, Like):
    __tablename__ = "venue_likes"

    venue = Column(Integer, ForeignKey("venues.id"), nullable=False)

