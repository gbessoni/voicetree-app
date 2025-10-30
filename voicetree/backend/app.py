"""
selfie.fm - FastAPI Backend
AI-Powered Link Sharing Platform with Voice Messages
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
from models import User, Link, ProfileView, LinkClick, VoiceMessage
from schemas import (
    UserCreate, UserResponse, LinkCreate, LinkResponse,
    ScrapeRequest, ScrapeResponse, UserCreateFromLinktree,
    VoiceCloneResponse, GenerateVoiceRequest, GenerateWelcomeRequest,
    VoiceMessageResponse
)
from scraper import scraper
from voice_ai import VoiceAIService
from datetime import datetime, timedelta
from sqlalchemy import func, desc

app = FastAPI(title="selfie.fm", description="AI-powered link sharing with voice messages")

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
    
    # Track profile view
    referrer = request.headers.get("referer", "direct")
    profile_view = ProfileView(user_id=user.id, referrer=referrer)
    db.add(profile_view)
    user.profile_views += 1
    db.commit()
    
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

# Analytics API Routes

@app.get("/api/admin/{username}/stats")
def get_dashboard_stats(username: str, db: Session = Depends(get_db)):
    """Get overview statistics for admin dashboard"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get views from last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_views = db.query(func.count(ProfileView.id)).filter(
        ProfileView.user_id == user.id,
        ProfileView.view_date >= thirty_days_ago
    ).scalar()
    
    # Calculate conversion rate
    conversion_rate = 0
    if user.profile_views > 0:
        conversion_rate = (user.total_link_clicks / user.profile_views) * 100
    
    return {
        "profile_views_30d": recent_views or 0,
        "total_link_clicks": user.total_link_clicks,
        "voice_message_plays": user.voice_message_plays,
        "conversion_rate": round(conversion_rate, 2)
    }

@app.get("/api/admin/{username}/views-chart")
def get_views_chart_data(username: str, db: Session = Depends(get_db)):
    """Get profile views over time for chart (last 30 days)"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # Group views by date
    views_by_date = db.query(
        func.date(ProfileView.view_date).label('date'),
        func.count(ProfileView.id).label('count')
    ).filter(
        ProfileView.user_id == user.id,
        ProfileView.view_date >= thirty_days_ago
    ).group_by(func.date(ProfileView.view_date)).all()
    
    # Create complete date range with zeros for missing dates
    date_counts = {str(v.date): v.count for v in views_by_date}
    labels = []
    data = []
    
    for i in range(30):
        date = (datetime.now() - timedelta(days=29-i)).date()
        labels.append(date.strftime("%m/%d"))
        data.append(date_counts.get(str(date), 0))
    
    return {
        "labels": labels,
        "data": data
    }

@app.get("/api/admin/{username}/clicks-chart")
def get_clicks_chart_data(username: str, db: Session = Depends(get_db)):
    """Get link clicks by link for bar chart (top 10)"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get top 10 links by click count
    top_links = db.query(Link).filter(
        Link.user_id == user.id
    ).order_by(desc(Link.click_count)).limit(10).all()
    
    labels = [link.title for link in top_links]
    data = [link.click_count for link in top_links]
    
    return {
        "labels": labels,
        "data": data
    }

@app.get("/api/admin/{username}/traffic-sources")
def get_traffic_sources(username: str, db: Session = Depends(get_db)):
    """Get traffic sources for pie chart"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # Group by referrer
    traffic = db.query(
        ProfileView.referrer,
        func.count(ProfileView.id).label('count')
    ).filter(
        ProfileView.user_id == user.id,
        ProfileView.view_date >= thirty_days_ago
    ).group_by(ProfileView.referrer).all()
    
    # Categorize traffic sources
    direct = 0
    social = 0
    other = 0
    
    social_domains = ['facebook', 'twitter', 'instagram', 'linkedin', 'tiktok', 'youtube']
    
    for t in traffic:
        if not t.referrer or t.referrer == 'direct':
            direct += t.count
        elif any(domain in t.referrer.lower() for domain in social_domains):
            social += t.count
        else:
            other += t.count
    
    return {
        "labels": ["Direct", "Social Media", "Other"],
        "data": [direct, social, other]
    }

@app.get("/api/admin/{username}/recent-clicks")
def get_recent_clicks(username: str, limit: int = 20, db: Session = Depends(get_db)):
    """Get recent link clicks for analytics table"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get recent clicks with link information
    recent_clicks = db.query(LinkClick).filter(
        LinkClick.user_id == user.id
    ).order_by(desc(LinkClick.click_date)).limit(limit).all()
    
    # Format the data
    clicks_data = []
    for click in recent_clicks:
        clicks_data.append({
            "id": click.id,
            "link_title": click.link.title if click.link else "Unknown",
            "link_url": click.link.url if click.link else "",
            "click_date": click.click_date.isoformat(),
            "referrer": click.referrer or "direct",
            "user_agent": click.user_agent or "Unknown"
        })
    
    return clicks_data

# Link Management API Routes

@app.put("/api/admin/{username}/links/{link_id}/toggle")
def toggle_link_active(username: str, link_id: int, db: Session = Depends(get_db)):
    """Toggle link active/inactive status"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    link = db.query(Link).filter(Link.id == link_id, Link.user_id == user.id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    link.is_active = not link.is_active
    db.commit()
    
    return {"is_active": link.is_active}

@app.put("/api/admin/{username}/links/reorder")
def reorder_links(username: str, link_orders: dict, db: Session = Depends(get_db)):
    """Reorder links - expects {"link_id": order} mapping"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for link_id, order in link_orders.items():
        link = db.query(Link).filter(Link.id == int(link_id), Link.user_id == user.id).first()
        if link:
            link.order = order
    
    db.commit()
    return {"message": "Links reordered successfully"}

@app.post("/api/clicks/{username}/{link_id}")
def track_link_click(
    username: str,
    link_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Track a link click with full analytics data"""
    # Get user
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get link
    link = db.query(Link).filter(Link.id == link_id, Link.user_id == user.id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    # Extract analytics data
    referrer = request.headers.get("referer", "direct")
    user_agent = request.headers.get("user-agent", "")
    
    # Increment counters
    link.click_count += 1
    user.total_link_clicks += 1
    
    # Record click event with full data
    click = LinkClick(
        link_id=link_id,
        user_id=user.id,
        referrer=referrer,
        user_agent=user_agent
    )
    db.add(click)
    db.commit()
    
    return {"message": "Click tracked", "link_id": link_id}

@app.post("/api/track/voice-play/{username}")
def track_voice_play(username: str, db: Session = Depends(get_db)):
    """Track a voice message play"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.voice_message_plays += 1
    db.commit()
    
    return {"message": "Voice play tracked"}

# Voice Message Approval API Routes

@app.get("/api/admin/{username}/pending-voices")
def get_pending_voice_messages(username: str, db: Session = Depends(get_db)):
    """Get pending voice messages for approval"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    pending = db.query(VoiceMessage).filter(
        VoiceMessage.user_id == user.id,
        VoiceMessage.is_approved == False,
        VoiceMessage.is_active == True
    ).order_by(desc(VoiceMessage.created_at)).all()
    
    return [{
        "id": vm.id,
        "text_content": vm.text_content,
        "audio_file_path": vm.audio_file_path,
        "created_at": vm.created_at.isoformat()
    } for vm in pending]

@app.put("/api/admin/{username}/voices/{voice_id}/approve")
def approve_voice_message(username: str, voice_id: int, db: Session = Depends(get_db)):
    """Approve a voice message"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    voice = db.query(VoiceMessage).filter(
        VoiceMessage.id == voice_id,
        VoiceMessage.user_id == user.id
    ).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice message not found")
    
    voice.is_approved = True
    voice.approved_at = datetime.now()
    db.commit()
    
    return {"message": "Voice message approved"}

@app.put("/api/admin/{username}/voices/{voice_id}/reject")
def reject_voice_message(username: str, voice_id: int, db: Session = Depends(get_db)):
    """Reject a voice message"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    voice = db.query(VoiceMessage).filter(
        VoiceMessage.id == voice_id,
        VoiceMessage.user_id == user.id
    ).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice message not found")
    
    voice.is_active = False
    db.commit()
    
    return {"message": "Voice message rejected"}

@app.put("/api/admin/{username}/auto-approve")
def toggle_auto_approve(username: str, db: Session = Depends(get_db)):
    """Toggle auto-approve setting for voice messages"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.auto_approve_voice = not user.auto_approve_voice
    db.commit()
    
    return {"auto_approve": user.auto_approve_voice}

# Profile Settings API Routes

@app.put("/api/admin/{username}/profile")
def update_profile_settings(
    username: str,
    display_name: str = Form(...),
    bio: str = Form(None),
    db: Session = Depends(get_db)
):
    """Update profile settings"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.display_name = display_name
    if bio is not None:
        user.bio = bio
    db.commit()
    
    return {"message": "Profile updated"}

@app.put("/api/admin/{username}/toggle-publish")
def toggle_publish(username: str, db: Session = Depends(get_db)):
    """Toggle profile publish status"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_published = not user.is_published
    db.commit()
    
    return {"is_published": user.is_published}

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
