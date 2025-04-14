from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from database import Base
from datetime import datetime


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    roomnumber = Column("roomNumber", String, unique=True, index=True)
    name = Column(String)
    quizmasterid = Column("quizmasterID", String)
    questionfile = Column("questionFile", String)
    answerfile = Column("answerFile", String)
    created_at = Column("createdAt", DateTime, default=datetime.utcnow)


class UsersAttended(Base):
    __tablename__ = "usersAttended"

    id = Column(Integer, primary_key=True, index=True)
    roomNumber = Column(String, ForeignKey("rooms.roomNumber"))
    studentName = Column(String, nullable=False)
    score = Column(Float, default=0.0)
