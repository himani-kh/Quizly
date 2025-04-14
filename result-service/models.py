from sqlalchemy import Column, Integer, String, Float
from database import Base

class UsersAttended(Base):
    __tablename__ = "usersAttended"

    id = Column(Integer, primary_key=True, index=True)
    roomNumber = Column(String, index=True)
    studentName = Column(String)
    score = Column(Float)
