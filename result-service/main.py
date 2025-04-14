from fastapi import FastAPI, Request, Depends, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pathlib import Path

from models import UsersAttended
from database import init_db, get_db
from auth import get_token_from_cookie, verify_access_token

app = FastAPI()

init_db()

BASE_DIR = Path(__file__).parent.resolve()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/get-scores", response_class=HTMLResponse)
async def get_scores(
    request: Request,
    roomNumber: str = Query(..., alias="room_number"),
    db: Session = Depends(get_db)
):
    token = get_token_from_cookie(request)

    user_email = verify_access_token(token)

    scores = db.query(UsersAttended).filter(UsersAttended.roomNumber == roomNumber).all()

    return templates.TemplateResponse("scores.html", {
        "request": request,
        "roomNumber": roomNumber,
        "scores": scores,
        "message": "No scores found for this room." if not scores else ""
    })
