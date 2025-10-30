# 🎙️ selfie.fm - Voice-Powered Link Sharing

**AI-Powered Link Sharing Platform with Voice Messages**

selfie.fm is a next-generation link-in-bio platform that adds your voice to every link you share. Create a personalized page with AI-powered voice messages that introduce each of your links.

## Features (Phase 1 - MVP)

✅ FastAPI backend with SQLite database  
✅ User profile model and link management  
✅ Basic routes: homepage and `/{username}` profile pages  
✅ Simple frontend HTML/CSS  

## Project Structure

```
voicetree/
├── backend/
│   ├── __init__.py
│   ├── app.py              # Main FastAPI application
│   ├── models.py           # SQLAlchemy models (User, Link)
│   ├── database.py         # Database configuration
│   └── schemas.py          # Pydantic schemas
├── frontend/
│   ├── templates/
│   │   ├── index.html      # Homepage
│   │   └── profile.html    # User profile page
│   └── static/
│       └── css/
│           └── style.css   # Styles
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

1. **Install dependencies:**
```bash
pip install -r voicetree/requirements.txt
```

2. **Run the application:**
```bash
cd voicetree/backend
python app.py
```

Or using uvicorn directly:
```bash
uvicorn voicetree.backend.app:app --reload
```

3. **Open your browser:**
```
http://localhost:8000
```

## Usage

### Create a User (API)

```bash
curl -X POST "http://localhost:8000/api/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "display_name": "John Doe",
    "bio": "Tech enthusiast and creator",
    "avatar_url": "https://example.com/avatar.jpg"
  }'
```

### Add Links (API)

```bash
curl -X POST "http://localhost:8000/api/users/johndoe/links" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Website",
    "url": "https://johndoe.com",
    "description": "Check out my personal website"
  }'
```

### View Profile

Visit: `http://localhost:8000/johndoe`

## API Endpoints

- `GET /` - Homepage
- `GET /{username}` - User profile page
- `POST /api/users` - Create a new user
- `GET /api/users/{username}` - Get user details
- `POST /api/users/{username}/links` - Add a link
- `GET /api/users/{username}/links` - Get all links

## Database

Uses SQLite database (`voicetree.db`) with two tables:
- **users**: User profiles
- **links**: User links

The database is automatically created on first run.

## Current Features

✅ User profiles with customizable bio and avatar
✅ Link management with voice messages
✅ AI voice cloning with ElevenLabs
✅ Click tracking and analytics
✅ Voice message plays tracking
✅ Dashboard with charts and stats
✅ Auto-approve voice messages
✅ Profile publishing controls
✅ Linktree import functionality

## Technology Stack

**Backend:**
- FastAPI - Modern Python web framework
- SQLAlchemy - SQL toolkit and ORM
- SQLite - Embedded database
- ElevenLabs API - AI voice cloning and generation

**Frontend:**
- HTML5/CSS3 - Modern responsive design
- Vanilla JavaScript - No framework dependencies
- Jinja2 - Template engine
- Chart.js - Analytics visualization

**Server:**
- Uvicorn - ASGI server

## Voice AI Features

selfie.fm uses ElevenLabs AI to provide:
- **Voice Cloning**: Clone your voice with 3 audio samples
- **Voice Messages**: Generate personalized voice intros for each link
- **Auto-Generation**: AI-powered voice message creation
- **Voice Testing**: Test your cloned voice before publishing

## Contributing

selfie.fm is built to help creators add personality to their link sharing. Feel free to contribute improvements and new features.

---

**Built with ❤️ using AI voice technology**
