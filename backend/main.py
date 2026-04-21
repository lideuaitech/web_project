from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from jose import JWTError, jwt
import logging
import shutil
import uuid
from pathlib import Path

# ===== LOCAL IMPORTS =====
from database import SessionLocal, engine, Base
from models import User, UserFile, ChatSession, Message
from connectors.csv_connector import CSVConnector
from ai_engine import AIEngine

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= APP =================
app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= DB INIT =================
Base.metadata.create_all(bind=engine)

# ================= SCHEMAS =================
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=2, max_length=50)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ================= DB =================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================= AUTH =================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# ================= AUTH ROUTES =================

<<<<<<< HEAD
#===== SIGNUP =====

@app.get("/api/health")
def hello():
    return {"message": "OK! All Good"}


# ===== SIGNUP =====
=======
>>>>>>> refs/remotes/origin/main
@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        email=user.email,
        password=hash_password(user.password),
        name=user.name,
        tenant_id="default"
    )

    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/dashboard")
def dashboard(user: str = Depends(get_current_user)):
    return {"message": f"Welcome {user}!"}

# ================= FILE UPLOAD =================

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if not file.filename.lower().endswith((".csv", ".xlsx")):
            raise HTTPException(status_code=400, detail="Only CSV/Excel allowed")

        unique_filename = f"{uuid.uuid4()}_{file.filename.replace(' ', '_')}"
        file_path = UPLOAD_FOLDER / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        new_file = UserFile(
            user_email=user,
            file_name=file.filename,
            file_path=f"uploads/{unique_filename}"
        )

        db.add(new_file)
        db.commit()

        return {
            "message": "Upload successful",
            "path": f"uploads/{unique_filename}"
        }

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ================= QUERY =================

@app.get("/query")
def query(
    file_path: str,
    question: str,
    chat_id: int = None,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        full_path = BASE_DIR / file_path

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        connector = CSVConnector(str(full_path))
        connector.connect()

        df = connector.df

        ai = AIEngine(df, None)
        result = ai.run(question)

        # ✅ UPDATE CHAT TITLE
        if chat_id:
            chat = db.query(ChatSession).filter(ChatSession.id == chat_id).first()
            if chat and chat.title == "New Chat":
                chat.title = question[:30]
                db.commit()

        return result

    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ================= PREVIEW =================

@app.get("/preview")
def preview(file_path: str, user: str = Depends(get_current_user)):
    try:
        full_path = BASE_DIR / file_path

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        connector = CSVConnector(str(full_path))
        connector.connect()

        df = connector.df

        if df is None or df.empty:
            return {"message": "File is empty"}

        return df.head(10).to_dict(orient="records")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================= FILE LIST =================

@app.get("/files")
def list_files(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    files = db.query(UserFile).filter(UserFile.user_email == user).all()

    return [
        {"id": f.id, "name": f.file_name, "path": f.file_path}
        for f in files
    ]

# ================= CREATE CHAT =================

@app.post("/chat/create")
def create_chat(
    file_path: str,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat = ChatSession(
        user_email=user,
        file_path=file_path,
        title="New CHat"
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return {"chat_id": chat.id}

# ================= GET CHAT =================

@app.get("/chat/list")
def get_chats(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    chats = db.query(ChatSession).filter(ChatSession.user_email == user).all()

    return [
        {"id": c.id, "title": c.title, "file_path": c.file_path}
        for c in chats
    ]

# ================= GET MESSAGE =================

@app.get("/chat/messages")
def get_messages(chat_id: int, db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(Message.session_id == chat_id).all()

    return [{"role": m.role, "content": m.content} for m in msgs]

# ================= SAVE MESSAGE =================

@app.post("/chat/message")
def save_message(chat_id: int, role: str, content: str, db: Session = Depends(get_db)):
    msg = Message(
        session_id=chat_id,
        role=role,
        content=content
    )
    db.add(msg)
    db.commit()

    return {"status": "saved"}

# ================= GLOBAL ERROR =================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"}
    )
