from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from schemas import QuizMasterCreate, QuizMasterLogin
from crud import create_quizmaster, authenticate_quizmaster
from models import QuizMaster
from pathlib import Path
from utils.token import create_access_token

app = FastAPI()

init_db()
# Mount static folder for CSS/JS
app.mount("/static", StaticFiles(directory="static"), name="static")
    
# Template setup
BASE_DIR = Path(__file__).parent.resolve()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

# Serve the homepage
@app.get("/index", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Serve the register page
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Serve the login page
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Handle registration form submission
@app.post("/register")
def register_user(
    request: Request,
    name: str = Form(...),  # ✅ Added name parameter
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(QuizMaster).filter(QuizMaster.email == email).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email already registered"})

    new_user = QuizMasterCreate(name=name, email=email, password=password)  # ✅ Pass name
    create_quizmaster(db, new_user)
    return RedirectResponse(url="/login", status_code=303)


@app.post("/login")
def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = QuizMasterLogin(email=email, password=password)
    quizmaster = authenticate_quizmaster(db, user)

    if not quizmaster:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    # Create JWT token
    token_data = {"sub": quizmaster.email}
    token = create_access_token(token_data)

    # Redirect to quiz_management_service dashboard
    response = RedirectResponse(url="http://localhost:8001/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,       # Prevent JS access — avoids XSS attacks
        max_age=1800,        # Optional: auto-expire after 30 minutes (in seconds)
        samesite="lax",      # Controls when the cookie is sent (safe default for most apps)
        secure=False         # Change to True if using HTTPS (required in production)
    )
    return response


@app.post("/api/login")
def api_login_user(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = QuizMasterLogin(email=email, password=password)
    quizmaster = authenticate_quizmaster(db, user)

    if not quizmaster:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = {"sub": quizmaster.email}
    token = create_access_token(token_data)
    print(token)
    return {"access_token": token, "token_type": "bearer"}

