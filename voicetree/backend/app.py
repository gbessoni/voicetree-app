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

from database import get_db, init_db
from models import User, Link
from schemas import UserCreate, UserResponse, LinkCreate, LinkResponse

app = FastAPI(title="VoiceTree", description="Linktree clone with AI voice features")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="voicetree/frontend/static"), name="static")
templates = Jinja2Templates(directory="voicetree/frontend/templates")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Homepage route
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Render the homepage"""
    return templates.TemplateResponse("index.html", {"request": request})

# User profile route
@app.get("/{username}", response_class=HTMLResponse)
async def user_profile(request: Request, username: str, db: Session = Depends(get_db)):
    """Render user profile page with their links"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    links = db.query(Link).filter(Link.user_id == user.id, Link.is_active == True).all()
    
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user, "links": links}
    )

# API Routes
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

@app.get("/api/users/{username}", response_model=UserResponse)
def get_user(username: str, db: Session = Depends(get_db)):
    """Get user by username"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
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

@app.get("/api/users/{username}/links", response_model=List[LinkResponse])
def get_user_links(username: str, db: Session = Depends(get_db)):
    """Get all links for a user"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    links = db.query(Link).filter(Link.user_id == user.id, Link.is_active == True).all()
    return links

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
