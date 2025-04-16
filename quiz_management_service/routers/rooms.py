from fastapi import APIRouter, Depends, File, UploadFile, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from utils.tokens import verify_access_token
from database import get_db
from models import Room
from datetime import datetime, timedelta, timezone
from pathlib import Path
import uuid
import shutil
import os

router = APIRouter()

# Jinja2 template setup
BASE_DIR = Path(__file__).parent.parent.resolve()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@router.post("/create-room")
def create_room(
    request: Request,
    name: str = Form(...),
    question_file: UploadFile = File(...),
    answer_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token in cookie")

    quizmaster_id = verify_access_token(token)

    shared_files_dir = "/code/files"
    os.makedirs(shared_files_dir, exist_ok=True)

    q_path = os.path.join(shared_files_dir, f"{uuid.uuid4()}_questions.csv")
    a_path = os.path.join(shared_files_dir, f"{uuid.uuid4()}_answers.csv")

    with open(q_path, "wb") as buffer:
        shutil.copyfileobj(question_file.file, buffer)
    with open(a_path, "wb") as buffer:
        shutil.copyfileobj(answer_file.file, buffer)

    room_number = str(uuid.uuid4())[:8]

    new_room = Room(
        roomNumber=room_number,
        name=name,
        quizmasterID=quizmaster_id,
        questionFile=q_path,
        answerFile=a_path,
        createdAt=datetime.now(timezone.utc)
    )
    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return templates.TemplateResponse("room_created.html", {
        "request": request,
        "room_number": room_number
    })


@router.get("/rooms/{quizmaster_id}")
def get_rooms(
    quizmaster_id: str, 
    request: Request, 
    db: Session = Depends(get_db)
):
    token = request.cookies.get("access_token")
    user_id = verify_access_token(token)    
    if user_id != quizmaster_id:
        raise HTTPException(status_code=403, detail="Access denied")

    rooms = db.query(Room).filter(Room.quizmasterID == quizmaster_id).all()
    return rooms


@router.get("/room/{room_number}")
def check_room(
    room_number: str, 
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.roomNumber == room_number).first()
    if not room:
        return {"exists": False}

    now = datetime.now(timezone.utc)
    if now - room.createdAt > timedelta(hours=24):
        return {"exists": False}

    return {"exists": True, "roomName": room.name}
