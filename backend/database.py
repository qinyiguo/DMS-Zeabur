import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Zeabur 會自動注入 DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

# 如果沒有 DATABASE_URL（本地開發），使用備用連接字串
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:postgres123@localhost:5432/factory_performance"

# 如果是 postgres:// 格式，轉換為 postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 依賴注入：獲取資料庫 session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
