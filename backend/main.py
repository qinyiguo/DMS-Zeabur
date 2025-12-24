from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import engine, Base
from routers import upload, reports, performance
import uvicorn
import os
from pathlib import Path

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

# 建立 static 資料夾（如果不存在）
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

# 掛載靜態檔案
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 註冊路由
app.include_router(upload.router, prefix="/api/upload", tags=["上傳"])
app.include_router(reports.router, prefix="/api/reports", tags=["報表"])
app.include_router(performance.router, prefix="/api/performance", tags=["業績"])

@app.get("/")
def read_root():
    return {"message": "廠業績管理系統 API", "status": "running"}

@app.get("/upload")
async def upload_page():
    """返回上傳頁面"""
    upload_html = static_dir / "upload.html"
    if upload_html.exists():
        return FileResponse(upload_html, media_type="text/html")
    return {"error": "上傳頁面不存在"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
