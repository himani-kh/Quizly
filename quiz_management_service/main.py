from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import Base, engine, init_db
from routers import rooms
from pathlib import Path
import os
from models import Room
from utils.tokens import verify_access_token
from sqlalchemy.orm import Session
from database import get_db

app = FastAPI()

# Initialize the database
init_db()

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Mount static files (e.g., CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates directory
BASE_DIR = Path(__file__).parent.resolve()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Include the rooms router
app.include_router(rooms.router)

# Route for dashboard
@app.get("/dashboard")
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Route for create-room page
@app.get("/create-room-page")
def create_room_page(request: Request):
    return templates.TemplateResponse("create_room.html", {"request": request})

# Route for view-rooms page
@app.get("/view-rooms-page")
def view_rooms_page(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not logged in")

    quizmaster_id = verify_access_token(token)
    rooms = db.query(Room).filter(Room.quizmasterID == quizmaster_id).all()

    return templates.TemplateResponse(
        "view_rooms.html",
        {"request": request, "rooms": rooms}
    )

# ✅ New route to show the created room number (used for redirection if needed)
@app.get("/room-created")
def room_created(request: Request, room_number: str):
    return templates.TemplateResponse("room_created.html", {
        "request": request,
        "room_number": room_number
    })
