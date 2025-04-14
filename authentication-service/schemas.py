from pydantic import BaseModel, Field
import re

class QuizMasterCreate(BaseModel):
    name: str
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str


class QuizMasterLogin(BaseModel):
    email: str
    password: str
