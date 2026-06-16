from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from jose import jwt
from difflib import get_close_matches

import logging
import shutil
import uuid
import pandas as pd
import traceback

from pathlib import Path

from database import SessionLocal, engine, Base
from models import User, UserFile, ChatSession, Message

from connectors.csv_connector import CSVConnector
from ai_engine import AIEngine

from excel_exporter import ExcelExporter
from pdf_exporter import PDFExporter
from ppt_exporter import PPTExporter

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

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str):
    return pwd_context.hash(password)



def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)



def create_access_token(data: dict):

    to_encode = data.copy()

    expire = (
        datetime.utcnow()
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")



def get_current_user(
    token: str = Depends(oauth2_scheme)
):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload.get("sub")

    except:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


# ================= CHAT TITLE =================


def update_chat_title(db, chat_id, question):

    if chat_id:

        chat = (
            db.query(ChatSession)
            .filter(ChatSession.id == chat_id)
            .first()
        )

        if (
            chat
            and (
                not chat.title
                or chat.title.lower() == "new chat"
            )
        ):

            title = question.strip().capitalize()

            if len(title) > 24:
                title = title[:24] + "..."

            chat.title = title
            db.commit()


# ================= AUTH ROUTES =================

@app.post("/signup")
def signup(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    existing = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    new_user = User(
        email=user.email,
        password=hash_password(user.password),
        name=user.name,
        tenant_id="default"
    )

    db.add(new_user)
    db.commit()

    return {
        "message": "User created successfully"
    }


@app.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):

    db_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if (
        not db_user
        or not verify_password(
            user.password,
            db_user.password
        )
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token(
        {"sub": db_user.email}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.get("/dashboard")
def dashboard(
    user: str = Depends(get_current_user)
):

    return {
        "message": f"Welcome {user}!"
    }


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

    unique_filename = (
        f"{uuid.uuid4()}_"
        f"{file.filename.replace(' ', '_')}"
    )

    file_path = UPLOAD_FOLDER / unique_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db.add(
        UserFile(
            user_email=user,
            file_name=file.filename,
            file_path=f"uploads/{unique_filename}"
        )
    )

    db.commit()

    return {
        "message": "Upload successful",
        "path": f"uploads/{unique_filename}"
    }


# ================= QUERY =================


def detect_intent(question):

    q = question.lower()

    if (
        "show all" in q
        or "list all" in q
        or "all regions" in q
        or "all categories" in q
        or "all products" in q
    ):
        return "distinct"

    if "top" in q:
        return "top_n"

    if "chart" in q or "graph" in q:
        return "chart"

    if " by " in q:
        return "group_by"

    if (
        "average" in q
        or "sum" in q
        or "total" in q
        or "max" in q
        or "min" in q
    ):
        return "aggregation"

    return "normal"



def find_best_column(question, columns):

    q_words = question.lower().split()

    lower_cols = [
        c.lower() for c in columns
    ]

    for word in q_words:

        matches = get_close_matches(
            word,
            lower_cols,
            n=1,
            cutoff=0.6
        )

        if matches:

            matched = matches[0]

            for original in columns:

                if original.lower() == matched:
                    return original

    return None


class QueryRequest(BaseModel):
    question: str
    file_path: str


@app.post("/query")
def query(
    request: QueryRequest,
    user: str = Depends(get_current_user)
):

    try:

        question = request.question

        file_path = request.file_path

        full_path = BASE_DIR / file_path
        if str(full_path).endswith(".csv"):
            df = pd.read_csv(full_path)
        else:
            df = pd.read_excel(full_path)

        engine = AIEngine(df)

        result = engine.run(question)

        return result

    except Exception as e:

        print("QUERY ERROR:")
        traceback.print_exc()

        return {
            "type": "text",
            "answer": str(e)
        }


# ================= CHAT =================

class ChatCreate(BaseModel):
    title: str
    file_path: str


@app.post("/chat/create")
def create_chat(
    payload: ChatCreate,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    chat = ChatSession(
        user_email=user,
        file_path=payload.file_path,
        title=payload.title
    )

    db.add(chat)

    db.commit()

    db.refresh(chat)

    return {
        "id": chat.id
    }

@app.get("/chat/list")
def get_chats(
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    chats = (
        db.query(ChatSession)
        .filter(ChatSession.user_email == user)
        .all()
    )

    return [
        {
            "id": c.id,
            "title": c.title,
            "file_path": c.file_path
        }
        for c in chats
    ]


@app.get("/chat/messages/{chat_id}")
def get_messages(
    chat_id: int,
    db: Session = Depends(get_db)
):

    msgs = (
        db.query(Message)
        .filter(Message.session_id == chat_id)
        .all()
    )

    return [
        {
            "role": m.role,
            "content": m.content
        }
        for m in msgs
    ]


class MessageRequest(BaseModel):
    chat_id: int
    role: str
    content: str


@app.post("/chat/message")
def save_message(
    request: MessageRequest,
    db: Session = Depends(get_db)
):

    try:

        msg = Message(
            session_id=request.chat_id,
            role=request.role,
            content=request.content
        )

        db.add(msg)

        db.commit()

        return {
            "message": "saved"
        }

    except Exception as e:

        print(
            "MESSAGE SAVE ERROR:",
            e
        )

        return {
            "error": str(e)
        }

    try:

        chat_id = request.chat_id
        role = request.role
        content = request.content

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO messages
            (chat_id, role, content)
            VALUES (%s, %s, %s)
            """,
            (
                chat_id,
                role,
                content
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        return {
            "message": "saved"
        }

    except Exception as e:

        print(
            "MESSAGE SAVE ERROR:",
            e
        )

        return {
            "error": str(e)
        }

    db.add(
        Message(
            session_id=chat_id,
            role=role,
            content=content
        )
    )

    db.commit()

    return {
        "status": "saved"
    }


@app.get("/files")
def get_files(
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    files = (
        db.query(UserFile)
        .filter(UserFile.user_email == user)
        .all()
    )

    return [
        {
            "name": f.file_name,
            "path": f.file_path
        }
        for f in files
    ]


# ================= ERROR =================

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):

    logger.error(
        f"Unhandled error: {str(exc)}"
    )

    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal Server Error"
        }
    )


# ================= EXPORTS =================

@app.post("/export/excel")
def export_excel(data: dict):

    if "data" in data:
        df = pd.DataFrame(data["data"])

    else:

        df = pd.DataFrame({
            "Label": data.get("labels", []),
            "Value": data.get("values", [])
        })

    summary = data.get(
        "summary",
        "No summary"
    )

    exporter = ExcelExporter(df, summary)

    file_path = exporter.export()

    return {
        "file": file_path
    }


app.mount(
    "/exports",
    StaticFiles(directory="exports"),
    name="exports"
)


@app.post("/export/pdf")
def export_pdf(data: dict):

    if "data" in data:
        df = pd.DataFrame(data["data"])

    else:

        df = pd.DataFrame({
            "Label": data.get("labels", []),
            "Value": data.get("values", [])
        })

    summary = data.get(
        "summary",
        "No summary"
    )

    exporter = PDFExporter(df, summary)

    file_path = exporter.export()

    return {
        "file": file_path
    }


@app.post("/export/ppt")
def export_ppt(data: dict):

    if "data" in data:
        df = pd.DataFrame(data["data"])

    else:

        df = pd.DataFrame({
            "Label": data.get("labels", []),
            "Value": data.get("values", [])
        })

    summary = data.get(
        "summary",
        "No summary"
    )

    exporter = PPTExporter(df, summary)

    file_path = exporter.export()

    return {
        "file": file_path
    }


# ================= HISTORY =================

@app.delete("/chat/clear")
def clear_history(
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    chats = (
        db.query(ChatSession)
        .filter(ChatSession.user_email == user)
        .all()
    )

    for chat in chats:

        db.query(Message).filter(
            Message.session_id == chat.id
        ).delete()

    db.query(ChatSession).filter(
        ChatSession.user_email == user
    ).delete()

    db.commit()

    return {
        "message": "History cleared"
    }


@app.delete("/chat/delete/{chat_id}")
def delete_chat(
    chat_id: int,
    db: Session = Depends(get_db)
):

    db.query(Message).filter(
        Message.session_id == chat_id
    ).delete()

    db.query(ChatSession).filter(
        ChatSession.id == chat_id
    ).delete()

    db.commit()

    return {
        "message": "Chat deleted"
    }


# ================= DATASET INFO =================

@app.get("/dataset/info")
def dataset_info(file_path: str):

    full_path = BASE_DIR / file_path

    if str(full_path).endswith(".csv"):
        df = pd.read_csv(full_path)

    elif str(full_path).endswith(".xlsx"):
        df = pd.read_excel(full_path)

    else:

        return {
            "rows": 0,
            "columns": 0
        }

    return {
        "rows": len(df),
        "columns": len(df.columns)
    }


# ================= DASHBOARD =================

@app.get("/generate-dashboard")
def generate_dashboard(file_path: str):

    full_path = BASE_DIR / file_path

    if str(full_path).endswith(".csv"):
        df = pd.read_csv(full_path)

    else:
        df = pd.read_excel(full_path)

    numeric_cols = (
        df.select_dtypes(include="number")
        .columns.tolist()
    )

    categorical_cols = (
        df.select_dtypes(include="object")
        .columns.tolist()
    )

    kpis = []

    if numeric_cols:

        first_num = numeric_cols[0]

        kpis.append({
            "title": f"Total {first_num}",
            "value": float(round(df[first_num].sum(), 2))
        })

        kpis.append({
            "title": f"Average {first_num}",
            "value": float(round(df[first_num].mean(), 2))
        })

        kpis.append({
            "title": f"Max {first_num}",
            "value": float(round(df[first_num].max(), 2))
        })

    charts = []

    if categorical_cols and numeric_cols:

        cat = categorical_cols[0]
        num = numeric_cols[0]

        grouped = (
            df.groupby(cat)[num]
            .sum()
            .reset_index()
        )

        charts.append({
            "chart_type": "bar",
            "title": f"{num} by {cat}",
            "labels": grouped[cat].astype(str).tolist(),
            "values": grouped[num].round(2).tolist()
        })

    if categorical_cols and numeric_cols:

        cat = categorical_cols[0]
        num = numeric_cols[0]

        grouped = (
            df.groupby(cat)[num]
            .mean()
            .reset_index()
        )

        charts.append({
            "chart_type": "pie",
            "title": f"Average {num} Distribution",
            "labels": grouped[cat].astype(str).tolist(),
            "values": grouped[num].round(2).tolist()
        })

    if len(numeric_cols) >= 1:

        num = numeric_cols[0]

        charts.append({
            "chart_type": "line",
            "title": f"{num} Trend",
            "labels": list(range(len(df.head(20)))),
            "values": (
                df[num]
                .head(20)
                .round(2)
                .tolist()
            )
        })

    insights = []

    if numeric_cols:

        num = numeric_cols[0]

        insights.append(
            f"Highest {num}: {df[num].max()}"
        )

        insights.append(
            f"Lowest {num}: {df[num].min()}"
        )

        insights.append(
            f"Average {num}: {round(df[num].mean(), 2)}"
        )

    return {
        "kpis": kpis,
        "charts": charts,
        "insights": insights
    }
