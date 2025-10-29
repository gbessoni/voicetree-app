"""
VoiceTree - FastAPI Backend
GitHub Issue #1: Build VoiceTree MVP - Core Features
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from sqlalchemy.orm import Session
from typing import List
import uvicorn
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

from database import get_db, init_db
from schemas import UserCreate, UserResponse, LinkCreate, LinkResponse, VoiceBioCreate, VoiceBioResponse
import crud

load_dotenv()

init_db()

app = FastAPI(title="VoiceTree", description="Linktree clone with AI voice features")

# Configure ElevenLabs API key
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
if not elevenlabs_api_key:
    raise ValueError("ELEVENLABS_API_KEY environment variable not set")

client = ElevenLabs(api_key=elevenlabs_api_key)

# Create audio directory if it doesn't exist
AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
templates = Jinja2Templates(directory="../frontend/templates")

# Homepage route
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Render the homepage"""
    return templates.TemplateResponse("index.html", {"request": request})

# User profile route
@app.get("/{username}", response_class=HTMLResponse)
async def user_profile(request: Request, username: str, db: Session = Depends(get_db)):
    """Render user profile page with their links"""
    user = crud.get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    links = crud.get_user_links(db, user_id=user.id)
    voice_bio = crud.get_approved_voice_bio(db, user_id=user.id)
    
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user, "links": links, "voice_bio": voice_bio}
    )

# API Routes
@app.post("/api/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    existing_user = crud.get_user_by_username(db, username=user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    return crud.create_user(db=db, user=user)

@app.get("/api/users/{username}", response_model=UserResponse)
def get_user(username: str, db: Session = Depends(get_db)):
    """Get user by username"""
    user = crud.get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/api/users/{username}/links", response_model=LinkResponse)
def create_link(username: str, link: LinkCreate, db: Session = Depends(get_db)):
    """Create a new link for a user"""
    user = crud.get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_user_link(db=db, link=link, user_id=user.id)

@app.get("/api/users/{username}/links", response_model=List[LinkResponse])
def get_user_links(username: str, db: Session = Depends(get_db)):
    """Get all links for a user"""
    user = crud.get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.get_user_links(db, user_id=user.id)

@app.post("/api/users/{username}/voice", response_model=VoiceBioResponse)
def create_or_update_voice_bio(username: str, voice_bio: VoiceBioCreate, db: Session = Depends(get_db)):
    """Create or update a voice bio for a user"""
    user = crud.get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_voice_bio = crud.create_or_update_voice_bio(db, voice_bio=voice_bio, user_id=user.id)

    # Generate audio using ElevenLabs
    try:
        audio = client.text_to_speech.convert(
            text=voice_bio.text,
            voice_id="Adam",
            model_id="eleven_multilingual_v2"
        )

        # Save audio to file
        audio_filename = f"{user.username}_{db_voice_bio.id}.mp3"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)

        with open(audio_path, "wb") as f:
            f.write(audio)

        db_voice_bio.audio_url = f"/{audio_path}"
        db.commit()
        db.refresh(db_voice_bio)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")

    return db_voice_bio

# Admin routes
@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db)):
    """Render the admin page with unapproved voice bios"""
    voice_bios = crud.get_unapproved_voice_bios(db)
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "voice_bios": voice_bios}
    )

@app.post("/admin/approve/{voice_bio_id}")
async def approve_voice_bio(voice_bio_id: int, db: Session = Depends(get_db)):
    """Approve a voice bio"""
    voice_bio = crud.approve_voice_bio(db, voice_bio_id=voice_bio_id)
    if not voice_bio:
        raise HTTPException(status_code=404, detail="Voice bio not found")

    return {"message": "Voice bio approved"}

@app.post("/admin/reject/{voice_bio_id}")
async def reject_voice_bio(voice_bio_id: int, db: Session = Depends(get_db)):
    """Reject a voice bio"""
    voice_bio = crud.reject_voice_bio(db, voice_bio_id=voice_bio_id)
    if not voice_bio:
        raise HTTPException(status_code=404, detail="Voice bio not found")
    
    # Optionally, delete the audio file
    if voice_bio.audio_url:
        audio_path = voice_bio.audio_url.lstrip("/")
        if os.path.exists(audio_path):
            os.remove(audio_path)

    return {"message": "Voice bio rejected"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
