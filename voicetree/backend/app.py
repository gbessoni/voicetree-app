"""
VoiceTree - FastAPI Backend
GitHub Issue #1: Build VoiceTree MVP - Core Features
"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi import Request
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

from database import get_db, init_db
from models import User, Link
from schemas import (
    UserCreate, UserResponse, LinkCreate, LinkResponse,
    ScrapeRequest, ScrapeResponse, UserCreateFromLinktree,
    VoiceCloneResponse, GenerateVoiceRequest, GenerateWelcomeRequest,
    VoiceMessageResponse
)
from scraper import scraper
from voice_ai import VoiceAIService

app = FastAPI(title="VoiceTree", description="Linktree clone with AI voice features")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
templates = Jinja2Templates(directory="../frontend/templates")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Homepage route
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Render the homepage"""
    return templates.TemplateResponse("index.html", {"request": request})

# Signup page route
@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Render the signup page"""
    return templates.TemplateResponse("signup.html", {"request": request})

# Preview page route
@app.get("/preview/{username}", response_class=HTMLResponse)
async def preview_page(request: Request, username: str, db: Session = Depends(get_db)):
    """Render the preview page for a user before publishing"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    links = db.query(Link).filter(Link.user_id == user.id, Link.is_active == True).all()
    
    return templates.TemplateResponse(
        "preview.html",
        {"request": request, "user": user, "links": links}
    )

# Dashboard page route
@app.get("/dashboard/{username}", response_class=HTMLResponse)
async def dashboard_page(request: Request, username: str, db: Session = Depends(get_db)):
    """Render the dashboard page for editing"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    links = db.query(Link).filter(Link.user_id == user.id, Link.is_active == True).all()
    
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user, "links": links}
    )

# User profile route
@app.get("/{username}", response_class=HTMLResponse)
async def user_profile(request: Request, username: str, db: Session = Depends(get_db)):
    """Render user profile page with their links"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only show published profiles
    if not user.is_published:
        raise HTTPException(status_code=404, detail="Profile not published yet")
    
    links = db.query(Link).filter(Link.user_id == user.id, Link.is_active == True).all()
    
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user, "links": links}
    )

# API Routes

@app.post("/api/scrape", response_model=ScrapeResponse)
def scrape_linktree(scrape_request: ScrapeRequest):
    """Scrape a Linktree URL and return the data"""
    try:
        data = scraper.scrape_linktree(scrape_request.linktree_url)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    db_user = User(
        username=user.username,
        display_name=user.display_name,
        bio=user.bio,
        avatar_url=user.avatar_url
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/users/from-linktree", response_model=UserResponse)
def create_user_from_linktree(user_data: UserCreateFromLinktree, db: Session = Depends(get_db)):
    """Create a new user with imported Linktree data"""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    db_user = User(
        username=user_data.username,
        display_name=user_data.display_name,
        bio=user_data.bio,
        imported_from_linktree=True,
        is_published=False
    )
    db.add(db_user)
    db.flush()
    
    # Add links
    for idx, link_data in enumerate(user_data.links):
        db_link = Link(
            user_id=db_user.id,
            title=link_data['title'],
            url=link_data['url'],
            order=idx
        )
        db.add(db_link)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/api/users/{username}", response_model=UserResponse)
def get_user(username: str, db: Session = Depends(get_db)):
    """Get user by username"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/api/preview/{username}", response_model=UserResponse)
def get_preview(username: str, db: Session = Depends(get_db)):
    """Get preview data for a user"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/api/users/{username}/publish")
def publish_profile(username: str, db: Session = Depends(get_db)):
    """Publish a user's profile"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_published = True
    db.commit()
    return {"message": "Profile published successfully"}

@app.put("/api/users/{username}")
def update_user(username: str, user_data: UserCreate, db: Session = Depends(get_db)):
    """Update user profile"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.display_name = user_data.display_name
    user.bio = user_data.bio
    if user_data.avatar_url:
        user.avatar_url = user_data.avatar_url
    
    db.commit()
    db.refresh(user)
    return user

@app.post("/api/users/{username}/links", response_model=LinkResponse)
def create_link(username: str, link: LinkCreate, db: Session = Depends(get_db)):
    """Create a new link for a user"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_link = Link(
        user_id=user.id,
        title=link.title,
        url=link.url,
        description=link.description
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

@app.put("/api/users/{username}/links/{link_id}", response_model=LinkResponse)
def update_link(username: str, link_id: int, link: LinkCreate, db: Session = Depends(get_db)):
    """Update a link"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_link = db.query(Link).filter(
        Link.id == link_id,
        Link.user_id == user.id
    ).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    db_link.title = link.title
    db_link.url = link.url
    if link.description:
        db_link.description = link.description
    
    db.commit()
    db.refresh(db_link)
    return db_link

@app.delete("/api/users/{username}/links/{link_id}")
def delete_link(username: str, link_id: int, db: Session = Depends(get_db)):
    """Delete a link"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_link = db.query(Link).filter(
        Link.id == link_id,
        Link.user_id == user.id
    ).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    db.delete(db_link)
    db.commit()
    return {"message": "Link deleted successfully"}

@app.get("/api/users/{username}/links", response_model=List[LinkResponse])
def get_user_links(username: str, db: Session = Depends(get_db)):
    """Get all links for a user"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    links = db.query(Link).filter(Link.user_id == user.id, Link.is_active == True).all()
    return links

# Voice AI Routes

@app.post("/api/voice/clone/{username}", response_model=VoiceCloneResponse)
async def create_voice_clone(
    username: str,
    voice_samples: List[UploadFile] = File(...),
    voice_name: str = Form(...),
    language: str = Form(default="en-US"),
    tags: str = Form(default=""),
    description: str = Form(default=""),
    remove_noise: bool = Form(default=True),
    db: Session = Depends(get_db)
):
    """
    Create voice clone from recorded samples using Inworld AI
    
    This endpoint handles the complete voice cloning process:
    1. Receives 1-3 voice samples from browser recording
    2. Sends samples to Inworld AI to create voice clone
    3. Saves voice_id to user profile
    4. Returns success with voice_id
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate number of samples
    if not voice_samples or len(voice_samples) == 0:
        raise HTTPException(status_code=400, detail="At least one voice sample is required")
    
    if len(voice_samples) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 voice samples allowed")
    
    # Read all uploaded files
    samples_data = []
    for sample in voice_samples:
        voice_data = await sample.read()
        
        # Validate file size per sample (5-15 seconds of audio, roughly 100KB-2MB)
        if len(voice_data) < 50000:  # Less than ~50KB
            raise HTTPException(status_code=400, detail=f"Voice sample '{sample.filename}' too short. Please record 5-15 seconds.")
        
        if len(voice_data) > 3000000:  # More than ~3MB
            raise HTTPException(status_code=400, detail=f"Voice sample '{sample.filename}' too large. Please keep under 20 seconds.")
        
        samples_data.append(voice_data)
    
    try:
        # Create voice clone with Inworld AI
        result = VoiceAIService.create_voice_clone(
            voice_samples=samples_data,
            voice_name=voice_name,
            language=language,
            tags=tags,
            description=description,
            remove_noise=remove_noise,
            username=username
        )
        
        if not result or not result.get("voice_id"):
            raise HTTPException(status_code=500, detail="Failed to create voice clone")
        
        # Update user with voice clone ID
        user.voice_clone_id = result["voice_id"]
        if result.get("sample_paths"):
            user.voice_sample_path = result["sample_paths"][0]  # Save first sample path
        db.commit()
        
        return VoiceCloneResponse(
            voice_id=result["voice_id"],
            sample_path=result.get("sample_paths", [None])[0],
            message=result.get("message", "Voice clone created successfully!")
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating voice clone: {str(e)}")


@app.post("/api/voice/test/{username}")
async def test_voice(
    username: str,
    text: str = Form(...),
    db: Session = Depends(get_db)
):
    """Test the user's cloned voice with custom text"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.voice_clone_id:
        raise HTTPException(status_code=400, detail="Voice clone not set. Please provide your voice ID first.")
    
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    if len(text) > 500:
        raise HTTPException(status_code=400, detail="Text too long. Maximum 500 characters for testing.")
    
    try:
        # Generate test audio
        audio_bytes = VoiceAIService.test_voice_clone(
            text=text,
            voice_id=user.voice_clone_id
        )
        
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Failed to generate test audio")
        
        # Return audio as response
        from fastapi.responses import Response
        return Response(content=audio_bytes, media_type="audio/mpeg")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing voice: {str(e)}")

@app.post("/api/voice/generate-link/{username}/{link_id}", response_model=VoiceMessageResponse)
async def generate_link_voice(
    username: str,
    link_id: int,
    request: GenerateVoiceRequest,
    db: Session = Depends(get_db)
):
    """Generate voice message for a specific link"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    link = db.query(Link).filter(Link.id == link_id, Link.user_id == user.id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if not user.voice_clone_id:
        raise HTTPException(status_code=400, detail="Voice clone not set up. Please upload a voice sample first.")
    
    try:
        # Delete old audio if exists
        if link.voice_message_audio:
            VoiceAIService.delete_audio_file(link.voice_message_audio)
        
        # Generate new voice message
        audio_path = VoiceAIService.generate_with_voice_clone(
            text=request.text,
            voice_id=user.voice_clone_id,
            user_id=user.id,
            purpose=f"link_{link_id}"
        )
        
        if not audio_path:
            raise HTTPException(status_code=500, detail="Failed to generate voice message")
        
        # Update link with voice message
        link.voice_message_text = request.text
        link.voice_message_audio = audio_path
        db.commit()
        
        return VoiceMessageResponse(
            audio_path=audio_path,
            text=request.text,
            message="Voice message generated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating voice: {str(e)}")

@app.delete("/api/voice/link/{username}/{link_id}")
async def delete_link_voice(
    username: str,
    link_id: int,
    db: Session = Depends(get_db)
):
    """Delete voice message from a link"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    link = db.query(Link).filter(Link.id == link_id, Link.user_id == user.id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if link.voice_message_audio:
        VoiceAIService.delete_audio_file(link.voice_message_audio)
        link.voice_message_text = None
        link.voice_message_audio = None
        db.commit()
    
    return {"message": "Voice message deleted successfully"}

@app.post("/api/voice/generate-welcome/{username}", response_model=VoiceMessageResponse)
async def generate_welcome_message(
    username: str,
    request: GenerateWelcomeRequest,
    db: Session = Depends(get_db)
):
    """Generate welcome message for user profile"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.voice_clone_id:
        raise HTTPException(status_code=400, detail="Voice clone not set up. Please upload a voice sample first.")
    
    try:
        # Delete old audio if exists
        if user.welcome_message_audio:
            VoiceAIService.delete_audio_file(user.welcome_message_audio)
        
        # Generate new welcome message
        audio_path = VoiceAIService.generate_with_voice_clone(
            text=request.text,
            voice_id=user.voice_clone_id,
            user_id=user.id,
            purpose="welcome"
        )
        
        if not audio_path:
            raise HTTPException(status_code=500, detail="Failed to generate welcome message")
        
        # Update user with welcome message
        user.welcome_message_text = request.text
        user.welcome_message_audio = audio_path
        user.welcome_message_type = request.message_type
        db.commit()
        
        return VoiceMessageResponse(
            audio_path=audio_path,
            text=request.text,
            message="Welcome message generated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating welcome message: {str(e)}")

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve audio files"""
    from pathlib import Path
    audio_path = Path(__file__).parent / "audio" / filename
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(audio_path, media_type="audio/mpeg")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
