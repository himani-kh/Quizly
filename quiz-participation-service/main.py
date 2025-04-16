from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os, csv
from pathlib import Path

from routers import attend
from models import Room, UsersAttended
from database import init_db, get_db
from utils.scoring import calculate_score

app = FastAPI()
app.include_router(attend.router)

init_db()

BASE_DIR = Path(__file__).parent.resolve()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

BASE_ANSWER_DIR = Path("temp_answers").resolve()


@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse("/join-room")

@app.get("/join-room", response_class=HTMLResponse)
async def join_room_form(request: Request):
    return templates.TemplateResponse("join_room.html", {"request": request})

@app.post("/join-room", response_class=HTMLResponse)
async def join_room_submit(
    request: Request,
    room_number: str = Form(...),
    student_name: str = Form(...),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.roomnumber == room_number).first()
    if not room or not os.path.exists(room.questionfile):
        return templates.TemplateResponse("join_room.html", {
            "request": request,
            "error": "Room not found or missing questions file."
        })

    return RedirectResponse(f"/question?qid=0&roomNumber={room_number}&studentName={student_name}", status_code=302)

@app.get("/question", response_class=HTMLResponse)
async def show_question(request: Request, qid: int, room_number: str, student_name: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.roomnumber == room_number).first()
    if not room or not os.path.exists(room.questionfile):
        return HTMLResponse("Questions file not found.", status_code=404)

    questions = []
    with open(room.questionfile, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            questions.append({"question": row[0], "options": row[1:]})

    if qid >= len(questions):
        return RedirectResponse(f"/submit-quiz?roomNumber={room_number}&studentName={student_name}", status_code=302)

    is_last = qid == len(questions) - 1

    return templates.TemplateResponse("questions.html", {
        "request": request,
        "qid": qid,
        "question": questions[qid],
        "roomNumber": room_number,
        "studentName": student_name,
        "is_last": is_last
    })


def secure_user_file_path(room_number: str, student_name: str) -> Path:
    filename = f"{room_number}_{student_name}.csv"
    full_path = (BASE_ANSWER_DIR / filename).resolve()
    if not str(full_path).startswith(str(BASE_ANSWER_DIR)):
        raise ValueError("Unsafe file path detected.")
    return full_path

@app.post("/question", response_class=HTMLResponse)
async def handle_question(
    request: Request,
    qid: int,
    roomNumber: str,
    studentName: str,
    answer: str = Form(...),
    is_last: bool = Form(False)
):
    os.makedirs(BASE_ANSWER_DIR, exist_ok=True)

    try:
        answer_file = secure_user_file_path(roomNumber, studentName)
    except ValueError:
        return HTMLResponse("Invalid filename.", status_code=400)

    with answer_file.open("a") as f:
        f.write(f"{answer}\n")

    if is_last:
        return RedirectResponse(
            f"/submit-quiz?roomNumber={roomNumber}&studentName={studentName}",
            status_code=302
        )

    return RedirectResponse(
        f"/question?qid={qid + 1}&roomNumber={roomNumber}&studentName={studentName}",
        status_code=302
    )

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

    try:
        answer_path = secure_user_file_path(roomNumber, studentName)
    except ValueError:
        return HTMLResponse("Invalid filename.", status_code=400)

    if not answer_path.exists():
        return HTMLResponse("No answers submitted.", status_code=400)

    with answer_path.open("r") as f:
        student_answers = [line.strip() for line in f.readlines()]

    score = calculate_score(student_answers, room.answerfile)

    db.add(UsersAttended(roomNumber=roomNumber, studentName=studentName, score=score))
    db.commit()

    answer_path.unlink()  # safely delete file

    return templates.TemplateResponse("result.html", {
        "request": request,
        "score": score,
        "studentName": studentName,
        "total": len(student_answers)
    })
