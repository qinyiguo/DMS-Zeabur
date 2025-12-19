import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# 優先使用 Zeabur 注入的連接字串
DATABASE_URL = os.getenv("POSTGRES_CONNECTION_STRING") or os.getenv("DATABASE_URL")

# 如果還是沒有，從個別環境變數組合
if not DATABASE_URL:
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB")
    
    # 只有在所有必要變數都存在時才組合
    if all([db_user, db_password, db_host, db_name]):
        DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        raise ValueError("無法獲取資料庫連接資訊，請檢查環境變數")

# 如果是 postgres:// 格式，轉換為 postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
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
