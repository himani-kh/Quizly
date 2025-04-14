from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os, csv

from routers import attend
from models import Room, UsersAttended
from database import init_db, get_db
from utils.scoring import calculate_score

app = FastAPI()
app.include_router(attend.router)

init_db()

BASE_DIR = Path(__file__).parent.resolve()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse("/join-room")

@app.get("/join-room", response_class=HTMLResponse)
async def join_room_form(request: Request):
    return templates.TemplateResponse("join_room.html", {"request": request})

@app.post("/join-room", response_class=HTMLResponse)
async def join_room_submit(
    request: Request,
    roomNumber: str = Form(...),
    studentName: str = Form(...),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.roomnumber == roomNumber).first()
    if not room or not os.path.exists(room.questionfile):
        return templates.TemplateResponse("join_room.html", {
            "request": request,
            "error": "Room not found or missing questions file."
        })

    return RedirectResponse(f"/question?qid=0&roomNumber={roomNumber}&studentName={studentName}", status_code=302)

@app.get("/question", response_class=HTMLResponse)
async def show_question(request: Request, qid: int, roomNumber: str, studentName: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.roomnumber == roomNumber).first()
    if not room or not os.path.exists(room.questionfile):
        return HTMLResponse("Questions file not found.", status_code=404)

    questions = []
    with open(room.questionfile, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            questions.append({"question": row[0], "options": row[1:]})

    if qid >= len(questions):
        return RedirectResponse(f"/submit-quiz?roomNumber={roomNumber}&studentName={studentName}", status_code=302)

    is_last = qid == len(questions) - 1

    return templates.TemplateResponse("questions.html", {
        "request": request,
        "qid": qid,
        "question": questions[qid],
        "roomNumber": roomNumber,
        "studentName": studentName,
        "is_last": is_last
    })

@app.post("/question", response_class=HTMLResponse)
async def handle_question(
    request: Request,
    qid: int,
    roomNumber: str,
    studentName: str,
    answer: str = Form(...),
    is_last: bool = Form(False)
):
    answer_file = f"temp_answers/{roomNumber}_{studentName}.csv"
    os.makedirs("temp_answers", exist_ok=True)
    with open(answer_file, "a") as f:
        f.write(f"{answer}\n")

    if is_last:
        return RedirectResponse(f"/submit-quiz?roomNumber={roomNumber}&studentName={studentName}", status_code=302)

    return RedirectResponse(f"/question?qid={qid + 1}&roomNumber={roomNumber}&studentName={studentName}", status_code=302)

@app.get("/submit-quiz", response_class=HTMLResponse)
async def submit_quiz(
    request: Request,
    roomNumber: str,
    studentName: str,
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.roomnumber == roomNumber).first()
    if not room or not os.path.exists(room.answerfile):
        return HTMLResponse("Invalid room or answer file missing.", status_code=400)

    answer_path = f"temp_answers/{roomNumber}_{studentName}.csv"
    if not os.path.exists(answer_path):
        return HTMLResponse("No answers submitted.", status_code=400)

    with open(answer_path, "r") as f:
        student_answers = [line.strip() for line in f.readlines()]

    score = calculate_score(student_answers, room.answerfile)
    db.add(UsersAttended(roomNumber=roomNumber, studentName=studentName, score=score))
    db.commit()
    os.remove(answer_path)

    return templates.TemplateResponse("result.html", {
        "request": request,
        "score": score,
        "studentName": studentName,
        "total": len(student_answers)
    })
