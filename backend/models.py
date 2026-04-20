import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    name = Column(String(100))
    tenant_id = Column(String(100), index=True)

class UserFile(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), index=True)
    file_name = Column(String(255))
    file_path = Column(String(255))

# ================= CHAT SESSION =================
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), index=True)
    file_path = Column(String(255))
    title = Column(String(255), default="New Chat")

# ================= MESSAGES =================
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, index=True)
    role = Column(String(50))  # "user" or "ai"
    content = Column(Text)
