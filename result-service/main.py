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
    room_number: str = Query(..., alias="room_number"),
    db: Session = Depends(get_db)
):
    token = get_token_from_cookie(request)

    user_email = verify_access_token(token)
    
    if not user_email:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    scores = db.query(UsersAttended).filter(UsersAttended.roomNumber == room_number).all()

    return templates.TemplateResponse("scores.html", {
        "request": request,
        "roomNumber": room_number,
        "scores": scores,
        "message": "No scores found for this room." if not scores else ""
    })
