import os
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import settings
from app.queue_manager import queue_manager
from app.plugins.manager import plugin_manager

app = FastAPI(
    title=settings.APP_NAME,
    description="Automated AI shorts trimmer, dynamic face reframer and subtitle burner backend."
)

# Enable CORS for desktop Electron shells and web interfaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folders for direct MP4 streaming in React player
app.mount("/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

class ProcessRequest(BaseModel):
    video_path: str
    aspect_ratio: str = "9:16"
    style_name: str = "TikTok"
    remove_silence: bool = False

@app.get("/")
@app.get("/api/health")
def read_root():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "models": {
            "whisper": settings.WHISPER_MODEL,
            "face_tracker": "opencv-haar-frontalface"
        },
        "directories": {
            "uploads": str(settings.UPLOAD_DIR),
            "outputs": str(settings.OUTPUT_DIR)
        }
    }

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """Receives local video files and stores them in backend/uploads/."""
    suffix = Path(file.filename).suffix
    if suffix.lower() not in [".mp4", ".mov", ".avi", ".mkv"]:
        raise HTTPException(status_code=400, detail="Unsupported video format. Use MP4, MOV, MKV or AVI.")

    save_name = f"{Path(file.filename).stem}_{os.urandom(4).hex()}{suffix}"
    save_path = settings.UPLOAD_DIR / save_name

    try:
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    return {
        "filename": file.filename,
        "saved_path": str(save_path),
        "video_url": f"/uploads/{save_name}"
    }

@app.post("/api/process")
async def process_video(request: ProcessRequest):
    """Enqueues a media task for speech transcription, framing analysis, and clip rendering."""
    if not os.path.exists(request.video_path):
        raise HTTPException(status_code=404, detail="Uploaded source video file not found on local disk.")
        
    job_id = queue_manager.submit_job(
        video_path=request.video_path,
        aspect_ratio=request.aspect_ratio,
        style_name=request.style_name,
        remove_silence=request.remove_silence
    )
    
    return {
        "job_id": job_id,
        "status": "enqueued",
        "message": "Task queued for asynchronous AI moment processing."
    }

@app.get("/api/status/{job_id}")
def get_status(job_id: str):
    """Returns the background processing progress and list of generated shorts."""
    status_info = queue_manager.get_job_status(job_id)
    if status_info.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="Job ID not recognized.")
    return status_info

@app.get("/api/plugins")
def get_plugins():
    """Returns the names and types of loaded custom AI plugins."""
    return {
        "loaded_plugins": [
            {
                "name": name,
                "type": p.plugin_type
            }
            for name, p in plugin_manager.plugins.items()
        ]
    }
