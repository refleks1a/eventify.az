from pydantic import BaseModel, EmailStr

from datetime import datetime, time


# User
class UserBase(BaseModel):
    username: str

    first_name: str
    last_name: str

class UserInfo(UserBase):
    id: int  
    is_organizer: bool  

class UserLogIn(BaseModel):
    username: str
    password: str    

class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    is_organizer: int

class Token (BaseModel):
    access_token: str
    token_type: str


# Venue

# Venue: VenueComment
class VenueCommentBase(BaseModel):
    venue: int

class VenueCommentCreate(VenueCommentBase):
    content: str 

class VenueCommentDelete(BaseModel):
    id: int    

class VenueCommentInfo(VenueCommentBase):
    id: int

    content: str
    owner_id: int
    owner: UserInfo

    created_at: time

# Venue: VenueLike
class VenueLikeBase(BaseModel):
    venue: int

class VenueLikeCreate(VenueLikeBase):
    pass 

class VenueLikeInfo(VenueLikeBase):
    id: int

    owner_id: int
    owner: UserInfo

    created_at: time

# Venue: Base    
class VenueBase(BaseModel):
    name: str
    description: str
    venue_type: str

    lat: str
    lng: str

    work_hours_open: time
    work_hours_close: time


class VenueCreate(VenueBase):
    pass

class VenueInfo(VenueBase):
    id: int

    num_likes: int
    comments: VenueCommentInfo


# Event

# Event: EventComment
class EventCommentBase(BaseModel):
    event: int

class EventCommentCreate(EventCommentBase):
    content: str 

class EventCommentDelete(BaseModel):
    id: int

class EventCommentInfo(EventCommentBase):
    id: int

    content: str
    owner_id: int
    owner: UserInfo

    created_at: time

# Event: EventLike
class EventLikeBase(BaseModel):
    event: int

class EventLikeCreate(EventLikeBase):
    pass 

class EventLikeInfo(EventLikeBase):
    id: int

    owner_id: int
    owner: UserInfo

    created_at: time

# Event: Base    
class EventBase(BaseModel):
    venue_id: int
    organizer_id: int

    title: str
    description: str
    event_type: str

    date: datetime
    start: time
    finish: time
    

class EventCreate(EventBase):
    poster_image_link: str

class EventInfo(EventBase):
    id: int

    num_likes: int
    comments: EventCommentInfo

    created_at: time
    
# Chat rooms

class ChatRoomBase(BaseModel):
    venue_id:int

    name: str

    max_capacity: int
    current_capacity: int
    status: bool

class ChatRoomCreate(ChatRoomBase):
    pass

class ChatRoomInfo(ChatRoomBase):
    id: int
    created_at: time

# Email

class EmailSchema(BaseModel):
    email:EmailStr
