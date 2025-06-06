from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from conn.database import DatabaseManager
from conn.utils import hash_password, verify_password
from bson import ObjectId
import logging
from jose import JWTError, jwt
import os
from mc_protocol import chat_with_mc
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
async def get_db() -> AsyncIOMotorDatabase:
    return DatabaseManager.get_database()

# Startup and shutdown events
@app.on_event("startup")
async def startup_db():
    try:
        await DatabaseManager.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_db():
    await DatabaseManager.close()
    logger.info("Database connection closed")

# Pydantic models for request/response
class UserBase(BaseModel):
    email: EmailStr
    preferences: dict = {"check_in_interval": 600, "theme": "light"}

class UserCreate(UserBase):
    password: str

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserInDB(UserBase):
    id: str
    password_hash: str
    salt: str
    created_at: datetime

class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    id: str
    user_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Helper functions for JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"email": token_data.email})
    if user is None:
        raise credentials_exception
    
    user["id"] = str(user.pop("_id"))
    return UserInDB(**user)

# Authentication endpoints
@app.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Update user creation endpoint
@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        # Check if user already exists
        if await db.users.find_one({"email": user.email}):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash the password
        password_hash, salt = hash_password(user.password)
        
        # Create user document
        user_doc = {
            "email": user.email,
            "password_hash": password_hash,
            "salt": salt,
            "created_at": datetime.now(timezone.utc),
            "preferences": user.preferences
        }
        
        result = await db.users.insert_one(user_doc)
        user_doc["id"] = str(result.inserted_id)
        
        return UserResponse(**user_doc)
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Update get_user endpoint to require authentication
@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        preferences=current_user.preferences,
        created_at=current_user.created_at
    )

# Update task endpoints to require authentication
@app.get("/tasks", response_model=List[TaskResponse])
async def get_user_tasks(
    status: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        # Build query
        query = {"user_id": ObjectId(current_user.id)}
        if status:
            query["status"] = status
        
        # Fetch tasks
        tasks = await db.tasks.find(query).to_list(1000)
        
        # Convert ObjectIds to strings
        for task in tasks:
            task["id"] = str(task.pop("_id"))
            task["user_id"] = str(task["user_id"])
        
        return [TaskResponse(**task) for task in tasks]
    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/tasks/all", response_model=List[TaskResponse])
async def get_all_tasks(
    status: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        # Build query
        query = {}
        if status:
            query["status"] = status
        
        # Fetch all tasks
        tasks = await db.tasks.find(query).to_list(1000)
        
        # Convert ObjectIds to strings
        for task in tasks:
            task["id"] = str(task.pop("_id"))
            task["user_id"] = str(task["user_id"])
        
        return [TaskResponse(**task) for task in tasks]
    except Exception as e:
        logger.error(f"Error fetching all tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Keep your existing chat endpoint
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    try:
        response = await chat_with_mc(request.message, current_user.id)
        return {"response": response}
    except HTTPException as e:
        # Re-raise HTTP exceptions (like timeouts) with their status codes
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request"
        )

# Password Reset Models
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

async def send_reset_email(email: str, reset_token: str):
    if not all([SMTP_USERNAME, SMTP_PASSWORD]):
        logger.error("SMTP credentials not configured")
        raise HTTPException(
            status_code=500,
            detail="Email service not configured"
        )
    
    reset_link = f"http://localhost:5173/reset-password?token={reset_token}"
    
    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = email
    msg['Subject'] = "Password Reset Request"
    
    body = f"""
    Hello,
    
    You have requested to reset your password. Click the link below to reset your password:
    {reset_link}
    
    This link will expire in 1 hour.
    
    If you did not request this password reset, please ignore this email.
    
    Best regards,
    Your App Team
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        logger.error(f"Failed to send reset email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send reset email"
        )

@app.post("/request-password-reset")
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await db.users.find_one({"email": request.email})
    if not user:
        # Don't reveal if the email exists or not
        return {"message": "If your email is registered, you will receive a password reset link"}
    
    # Generate a secure reset token
    reset_token = secrets.token_urlsafe(32)
    reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store the reset token in the database
    await db.users.update_one(
        {"email": request.email},
        {
            "$set": {
                "reset_token": reset_token,
                "reset_token_expiry": reset_token_expiry
            }
        }
    )
    
    # Send reset email
    await send_reset_email(request.email, reset_token)
    
    return {"message": "If your email is registered, you will receive a password reset link"}

@app.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    # Find user with the reset token
    user = await db.users.find_one({
        "reset_token": reset_data.token,
        "reset_token_expiry": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )
    
    # Hash the new password
    password_hash, salt = hash_password(reset_data.new_password)
    
    # Update the password and clear reset token
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_hash": password_hash,
                "salt": salt
            },
            "$unset": {
                "reset_token": "",
                "reset_token_expiry": ""
            }
        }
    )
    
    return {"message": "Password has been reset successfully"}

# teri maa ki chut
# teri bhenchod ki chut
# teri maa ki chut
# teri bhenchod ki chut
# maa ka bhosda
# tere baap ka bhosda
# tere bhenchod ka bhosda
# tere maa ka bhosda
# tere baap ka bhosda
# tere bhenchod ka bhosda
# tere maa ka bhosda
# tere baap ka bhosda
# tere bhenchod ka bhosda
# tere maa ka bhosda
# tere baap ka bhosda
# tere bhenchod ka bhosda
# tere maa ka bhosda
# tere baap ka bhosda
# tere bhenchod ka bhosda
# tere maa ka bhosda
# tere baap ka bhosda
# tere bhenchod ka bhosda