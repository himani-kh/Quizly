from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Room, UsersAttended
from utils.scoring import calculate_score
import os
import csv
import pandas as pd

router = APIRouter()

@router.post("/join-room-api")
def join_room_api(room_number: str, student_name: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.roomnumber == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found or expired")
    return {"message": "Room joined successfully"}

@router.get("/questions/{roomNumber}")
def get_questions(room_number: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.roomnumber == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    question_file = room.questionfile
    if not os.path.exists(question_file):
        raise HTTPException(status_code=500, detail="Questions file missing")

    questions = []
    df = pd.read_csv(question_file, skiprows=1, header=None)
    df = df.iloc[:, 1:]  # Drop the first column

    questions = df.values.tolist() # From column index 1 to end

    return {"questions": questions}

@router.post("/submit-quiz-api")
def submit_quiz_api(room_number: str, student_name: str, answers: list, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.roomnumber == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    score = calculate_score(answers, room.answerfile)
    db.add(UsersAttended(roomNumber=room_number, studentName=student_name, score=score))
    db.commit()
    return {"message": "Quiz submitted", "score": score}
