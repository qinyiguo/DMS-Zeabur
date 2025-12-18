from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import upload, reports, performance
import uvicorn

# 建立資料表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="廠業績管理系統 API")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(upload.router, prefix="/api/upload", tags=["上傳"])
app.include_router(reports.router, prefix="/api/reports", tags=["報表"])
app.include_router(performance.router, prefix="/api/performance", tags=["業績"])

@app.get("/")
def read_root():
    return {"message廠業績管理系統 API", "status": "running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
