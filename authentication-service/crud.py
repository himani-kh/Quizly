from sqlalchemy.orm import Session
from models import QuizMaster
from auth import hash_password, verify_password, create_access_token
from schemas import QuizMasterCreate, QuizMasterLogin

def create_quizmaster(db: Session, user: QuizMasterCreate):
    db_user = QuizMaster(name=user.name, email=user.email, password=user.password)  # No hashing
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_quizmaster(db: Session, user: QuizMasterLogin):
    db_user = db.query(QuizMaster).filter(QuizMaster.email == user.email).first()
    print(f"DB User: {db_user}")  # Debugging
    
    if db_user:
        print(f"Stored Password: {db_user.password}, Entered Password: {user.password}")  # Debugging
    
    if db_user and user.password == db_user.password:  
        return db_user
    
    return None
