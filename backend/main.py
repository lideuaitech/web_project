from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from fastapi.requests import Request

from sqlalchemy.orm import Session

from pydantic import BaseModel, EmailStr, Field

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

from database import SessionLocal, engine, Base
from models import User

from connectors.csv_connector import CSVConnector

import shutil
import os
import logging

from query_engine import QueryEngine
from ai_engine import AIEngine


# ===== LOGGING =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== APP =====
app = FastAPI()

# ===== CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # keep for MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== CREATE TABLES =====
Base.metadata.create_all(bind=engine)

# ===== SCHEMA =====
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=2, max_length=50)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ===== DB DEPENDENCY =====
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===== PASSWORD HASHING =====
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password[:72])


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# ===== JWT CONFIG =====
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ===== SIGNUP =====
@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

    hashed_password = hash_password(user.password)

    new_user = User(
        email=user.email,
        password=hashed_password,
        name=user.name,
        tenant_id="default"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"[SIGNUP] New user registered: {user.email}")

    return {"message": "User created successfully"}


# ===== LOGIN =====
@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(data={"sub": db_user.email})

    logger.info(f"[LOGIN] User logged in: {db_user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "name": db_user.name
    }


# ===== AUTH SYSTEM =====
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        return email

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# ===== PROTECTED ROUTE =====
@app.get("/dashboard")
def dashboard(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user).first()

    logger.info(f"[DASHBOARD] Accessed by: {user}")

    return {"message": f"Welcome {db_user.name}!"}


# ===== GLOBAL ERROR HANDLER =====
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Something went wrong", "error": str(exc)}
    )


# ===== TEST DB =====
@app.get("/test-db")
def test_db():
    from connectors.postgres_connector import PostgresConnector

    connector = PostgresConnector(
        host="127.0.0.1",
        database="postgres",
        user="postgres",
        password="root123"
    )

    result = connector.test()

    return {"result": result}


# ===== FILE UPLOAD SETUP =====
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ===== FILE UPLOAD API =====
@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    file_path = f"{UPLOAD_FOLDER}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": file.filename, "path": file_path}


# ===== CSV PREVIEW API =====
@app.get("/preview")
def preview_data(file_path: str):
    connector = CSVConnector(file_path)

    if not connector.connect():
        return {"error": "Failed to read file"}

    return {
        "columns": connector.fetch_schema(),
        "preview": connector.run_query()
    }


@app.get("/query")
def query_data(file_path: str, question: str):
    connector = CSVConnector(file_path)

    if not connector.connect():
        return {"error": "Failed to read file"}

    df = connector.df

    engine = QueryEngine(df)
    result = engine.run(question)

    return {
        "question": question,
        "result": result
    }

@app.get("/ai-query")
def ai_query(file_path: str, question: str):
    connector = CSVConnector(file_path)

    if not connector.connect():
        return {"error": "Failed to read file"}

    engine = AIEngine(connector.df)
    result = engine.run(question)

    return result
