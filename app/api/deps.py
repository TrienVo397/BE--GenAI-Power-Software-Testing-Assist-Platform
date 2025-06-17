from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db

def get_current_user(db: Session = Depends(get_db)):
    # Placeholder for user retrieval logic
    user = None  # Replace with actual user retrieval logic
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_db_session():
    db = get_db()
    try:
        yield db
    finally:
        db.close()