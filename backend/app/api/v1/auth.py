from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.models import User, ActivityHistory
from app.schemas.schemas import UserCreate, UserLogin, Token, UserResponse
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists"
        )
    
    # Hash password securely
    hashed_pwd = hash_password(user_in.password)
    
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name or user_in.email.split("@")[0],
        role=user_in.role or "regular_user",
        is_active=True,
        is_verified=True # Auto-verify for streamlined dev/prod use
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Record Activity History
    activity = ActivityHistory(
        user_id=new_user.id,
        activity_type="register",
        description=f"User {new_user.email} registered an account.",
        status="success"
    )
    db.add(activity)
    db.commit()
    
    # Generate JWT
    token_payload = {
        "user_id": new_user.id,
        "email": new_user.email,
        "role": new_user.role
    }
    access_token = create_access_token(token_payload)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role
        }
    }

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is deactivated. Please contact support."
        )
        
    # Log login activity
    activity = ActivityHistory(
        user_id=user.id,
        activity_type="login",
        description=f"User {user.email} logged in successfully.",
        status="success"
    )
    db.add(activity)
    db.commit()
    
    token_payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }
    access_token = create_access_token(token_payload)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
