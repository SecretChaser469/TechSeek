import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from . import models, schemas

# JWT Settings
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_key_123_change_me_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Email restriction (configurable)
ALLOWED_EMAIL_DOMAIN = os.getenv("ALLOWED_EMAIL_DOMAIN", "college.edu")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

router = APIRouter(prefix="/api/auth", tags=["auth"])

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        if email is None or user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email, role=role, user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user

def require_role(roles: list[str]):
    def dependency(current_user: models.User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return dependency

@router.post("/signup", response_model=schemas.Token)
def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # Verify email domain
    email_domain = user_in.email.split("@")[-1]
    if email_domain.lower() != ALLOWED_EMAIL_DOMAIN.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration only allowed for users with @{ALLOWED_EMAIL_DOMAIN} email domains.",
        )
    
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )

    # Hash the password
    hashed_pass = get_password_hash(user_in.password)
    
    # Create the user
    new_user = models.User(
        email=user_in.email,
        hashed_password=hashed_pass,
        role=user_in.role,
        name=user_in.name,
        semester=user_in.semester,
        branch=user_in.branch,
        bio_short=user_in.bio_short,
        bio_full=user_in.bio_full,
        streak_count=1,  # Set initial streak
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log initial streak log
    streak_log = models.StreakLog(
        user_id=new_user.id,
        date=datetime.utcnow().date(),
        activity_type="login"
    )
    db.add(streak_log)
    db.commit()

    # If faculty, create an empty specialization
    if new_user.role == "faculty":
        spec = models.FacultySpecialization(
            faculty_id=new_user.id,
            domain="General & Research Guidance",
            publications_json=[]
        )
        db.add(spec)
        db.commit()

    # Generate token
    token_payload = {"sub": new_user.email, "user_id": new_user.id, "role": new_user.role}
    token = create_access_token(data=token_payload)

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": new_user.role,
        "user_id": new_user.id
    }

@router.post("/login", response_model=schemas.Token)
def login(login_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == login_in.email).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update streak logic on successful login if it's a new day
    today = datetime.utcnow().date()
    streak_logged_today = db.query(models.StreakLog).filter(
        models.StreakLog.user_id == user.id,
        models.StreakLog.date == today
    ).first()

    if not streak_logged_today:
        yesterday = today - timedelta(days=1)
        streak_logged_yesterday = db.query(models.StreakLog).filter(
            models.StreakLog.user_id == user.id,
            models.StreakLog.date == yesterday
        ).first()

        if streak_logged_yesterday:
            # Active streak continued
            user.streak_count += 1
        else:
            # Streak broken, reset
            user.streak_count = 1

        db.add(models.StreakLog(user_id=user.id, date=today, activity_type="login"))
        db.commit()

    token_payload = {"sub": user.email, "user_id": user.id, "role": user.role}
    token = create_access_token(data=token_payload)

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id
    }
