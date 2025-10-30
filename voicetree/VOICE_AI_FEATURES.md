# Voice AI Customization Features

## Overview
Added comprehensive voice AI customization to VoiceTree dashboard using ElevenLabs API. Users can now clone their voice and create personalized voice messages for their profile and links.

## Features Added

### 1. Voice Clone Setup (One-time)
- **Location**: `/dashboard/{username}` - Voice Clone Setup section
- **Functionality**:
  - Upload 30-60 seconds of voice sample (MP3/WAV)
  - Creates personalized voice clone via ElevenLabs API
  - Stores voice_id in user profile
  - Shows status: "Voice Clone Ready ✓" or "Upload Voice Sample"
- **API Endpoint**: `POST /api/voice/clone/{username}`

### 2. Per-Link Voice Messages
- **Location**: Each link in dashboard has voice message controls
- **Functionality**:
  - Add 10-second voice intro to any link
  - Input text (max 200 characters, ~50 words)
  - Generate audio using cloned voice
  - Preview audio player
  - Edit or delete voice messages
- **API Endpoints**: 
  - `POST /api/voice/generate-link/{username}/{link_id}`
  - `DELETE /api/voice/link/{username}/{link_id}`

### 3. Welcome Message
- **Location**: `/dashboard/{username}` - Welcome Message section
- **Functionality**:
  - Create welcome message for profile page
  - Custom text input (max 500 characters)
  - Two options: Static or Daily AI (coming soon)
  - Preview and regenerate
- **API Endpoint**: `POST /api/voice/generate-welcome/{username}`

## Database Changes

### User Model
Added fields:
- `voice_clone_id`: Stores ElevenLabs voice ID
- `voice_sample_path`: Path to uploaded voice sample
- `welcome_message_text`: Welcome message text
- `welcome_message_audio`: Path to welcome audio file
- `welcome_message_type`: "static" or "daily_ai"

### Link Model
Added fields:
- `voice_message_text`: Link intro text
- `voice_message_audio`: Path to link intro audio file

## Files Modified

### Backend
1. `voicetree/backend/models.py` - Updated User and Link models
2. `voicetree/backend/voice_ai.py` - Added voice cloning and generation methods
3. `voicetree/backend/schemas.py` - Added voice API schemas
4. `voicetree/backend/app.py` - Added voice API endpoints

### Frontend
1. `voicetree/frontend/templates/dashboard.html` - Added UI for all voice features

## API Endpoints

### Voice Clone
```
POST /api/voice/clone/{username}
- Body: FormData with voice_sample file
- Response: VoiceCloneResponse with voice_id
```

### Generate Link Voice
```
POST /api/voice/generate-link/{username}/{link_id}
- Body: { "text": "message text" }
- Response: VoiceMessageResponse with audio_path
```

### Delete Link Voice
```
DELETE /api/voice/link/{username}/{link_id}
- Response: { "message": "success" }
```

### Generate Welcome Message
```
POST /api/voice/generate-welcome/{username}
- Body: { "text": "welcome text", "message_type": "static" }
- Response: VoiceMessageResponse with audio_path
```

### Serve Audio Files
```
GET /audio/{filename}
- Returns: Audio file (MP3)
```

## Environment Variables Required

```bash
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

## Usage Flow

1. **First Time Setup**:
   - User goes to dashboard
   - Uploads 30-60 second voice sample
   - System creates voice clone with ElevenLabs
   - Voice clone ready indicator appears

2. **Adding Link Voice Messages**:
   - User clicks "Add Voice Message" on a link
   - Enters text describing why to click the link
   - System generates audio using cloned voice
   - Audio player appears with preview
   - Can edit or delete voice message

3. **Creating Welcome Message**:
   - User enters welcome text in form
   - Selects message type (static/daily AI)
   - System generates audio using cloned voice
   - Audio player appears on profile page
   - Can regenerate with different text

## Audio Storage

All audio files are stored in:
- Voice samples: `voicetree/backend/audio/voice_samples/`
- Generated audio: `voicetree/backend/audio/`

Audio files are named with format: `{purpose}_{user_id}_{random_id}.mp3`

## Dashboard UI Sections

1. **Voice Clone Setup** (Top section)
   - Shows status or upload form
   - File upload for voice sample
   - Creates voice clone on submit

2. **Welcome Message** (Second section)
   - Only visible after voice clone setup
   - Text input with character counter
   - Message type selector
   - Audio preview if exists
   - Generate/delete buttons

3. **Links Section** (Modified)
   - Each link has voice message controls
   - "Add Voice Message" button if none
   - Audio preview + Edit/Delete if exists
   - Inline form for adding/editing voice text

## Technical Notes

- Voice samples validated: 100KB - 5MB file size
- Link voice messages limited to 200 characters
- Welcome messages limited to 500 characters
- All audio generated in MP3 format
- Old audio files deleted when regenerating
- Page reloads after successful voice generation
- Loading states shown during API calls

## Next Steps / Future Enhancements

1. Implement daily AI-generated welcome messages
2. Add voice message deletion for welcome message
3. Add bulk voice generation for all links
4. Add voice preview before saving
5. Support multiple voice clones per user
6. Add voice analytics (play counts)
7. Add voice customization (speed, pitch, etc.)

## Testing

To test the implementation:

1. Set `ELEVENLABS_API_KEY` environment variable
2. Start the server: `python app.py` from backend directory
3. Navigate to `/dashboard/{username}`
4. Test voice clone upload
5. Test link voice message generation
6. Test welcome message generation
7. Verify audio playback
8. Test edit/delete functionality

## Dependencies

The implementation uses:
- ElevenLabs Python SDK (v0.2.27)
- FastAPI file upload support
- SQLAlchemy for database
- Jinja2 templates for UI
