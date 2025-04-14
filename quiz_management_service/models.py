from sqlalchemy import Column, String, Integer, DateTime
from database import Base
from datetime import datetime

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    roomNumber = Column(String, unique=True, index=True)
    name = Column(String)
    quizmasterID = Column(String, index=True)
    questionFile = Column(String)
    answerFile = Column(String)
    createdAt = Column(DateTime, default=datetime.utcnow)
