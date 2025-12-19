import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# 優先使用 DATABASE_URL（Zeabur 自動注入）
DATABASE_URL = os.getenv("DATABASE_URL")

# 如果沒有 DATABASE_URL，從個別環境變數組合
if not DATABASE_URL:
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "1qaz@WSX")
    db_host = os.getenv("POSTGRES_HOST", "postgresql")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "factory_performance")
    
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

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
