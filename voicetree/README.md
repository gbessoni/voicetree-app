# 🌳 VoiceTree - MVP

**GitHub Issue #1: Build VoiceTree MVP - Core Features**

VoiceTree is a Linktree clone with AI voice features. Share all your important links from a single, customizable page.

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

## Next Steps (Future Phases)

- User authentication
- Link analytics
- AI voice features for link descriptions
- Custom themes and styling
- Link reordering
- QR code generation

## Development

Built with:
- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: HTML, CSS, Jinja2
- **Server**: Uvicorn

---

**Reference**: GitHub Issue #1 - Build VoiceTree MVP - Core Features
