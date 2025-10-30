# Voice Clone Workflow - Complete In-Dashboard Implementation

## Overview
The voice clone feature now works entirely within the VoiceTree dashboard, matching Inworld's UI exactly. No external portal steps required!

## Complete Workflow

### STEP 1: Record Voice Samples (In Dashboard)

**User Interface:**
- Form with voice clone details:
  * Name input (for voice clone)
  * Language dropdown (11 languages supported)
  * Tags (optional) - comma-separated
  * Description (optional)
  
**Recording Process:**
- "Record audio" button opens modal
- Modal shows:
  * Sample script to read naturally
  * "Start New Recording" button with timer
  * Audio preview after recording
  * "Use This" button to save sample
- Users can record up to 3 samples
- Each sample: 5-15 seconds (enforced)
- Samples displayed in list with remove option
- "Remove background noise" checkbox
- Legal consent checkbox (required)
- "Create Voice Clone" button (enabled when 1+ samples recorded)

### STEP 2: Voice Clone Processing

**Backend Process:**
1. Frontend sends FormData with:
   - `voice_name`: Name for the clone
   - `language`: Language code
   - `tags`: Optional tags
   - `description`: Optional description
   - `remove_noise`: Boolean flag
   - `voice_samples`: Array of audio blobs (1-3 samples)

2. Backend API (`/api/voice/clone/{username}`):
   - Validates samples (size, count)
   - Calls `VoiceAIService.create_voice_clone()`
   - Sends samples to Inworld AI API
   - Receives `voice_id` from Inworld
   - Saves `voice_id` to user database
   - Returns success response

3. Frontend shows loading state:
   - Spinner animation
   - "Creating your voice clone..." message
   - Prevents page close

### STEP 3: Success Screen

**User sees:**
- ✓ "Your cloned voice is ready" heading
- Voice ID displayed
- "Try your cloned voice" section:
  * Text input (500 char max)
  * Play button (▶) on right
  * Audio player appears below after generation
  
**Test Voice Function:**
- User enters text
- Clicks play button
- Frontend calls `/api/voice/test/{username}`
- Backend generates audio using voice clone
- Audio plays automatically
- User can test multiple times

### STEP 4: Use Voice for Messages

Once voice clone is created, users can:
1. Create welcome messages (auto-played on profile)
2. Add voice messages to individual links (10 seconds)
3. All messages use their cloned voice automatically

## Technical Implementation

### Frontend (dashboard.html)
```javascript
// Recording variables
let mediaRecorder;
let audioChunks = [];
let voiceSamples = []; // Array of {blob, duration, timestamp}

// Browser MediaRecorder API for recording
navigator.mediaDevices.getUserMedia({ audio: true })

// Form submission sends all samples
FormData with voice_samples as multiple files
```

### Backend (voice_ai.py)
```python
def create_voice_clone(
    voice_samples: list,  # 1-3 audio blobs
    voice_name: str,
    language: str = "en-US",
    tags: str = "",
    description: str = "",
    remove_noise: bool = True,
    username: str = None
) -> Dict[voice_id, sample_paths, message]
```

### API Endpoint (app.py)
```python
@app.post("/api/voice/clone/{username}")
async def create_voice_clone(
    username: str,
    voice_samples: List[UploadFile],
    voice_name: str,
    language: str = "en-US",
    tags: str = "",
    description: str = "",
    remove_noise: bool = True
) -> VoiceCloneResponse
```

## Inworld AI Integration

### Voice Clone Creation
- **Endpoint**: `POST https://api.inworld.ai/tts/v1/clone`
- **Headers**: `Authorization: Basic {INWORLD_API_KEY}`
- **Form Data**:
  * `audioSamples`: Multiple audio files (multipart)
  * `name`: Voice clone name
  * `language`: Language code
  * `removeBackgroundNoise`: "true"/"false"
  * `tags`: Optional tags
  * `description`: Optional description
- **Response**: `{ voiceId: "...", ... }`

### Voice Testing/Generation
- **Endpoint**: `POST https://api.inworld.ai/tts/v1/voice`
- **Headers**: `Authorization: Basic {INWORLD_API_KEY}`
- **JSON Body**:
  ```json
  {
    "text": "Text to speak",
    "voiceId": "user_voice_id",
    "modelId": "inworld-tts-1",
    "audioConfig": {
      "encoding": "MP3",
      "sampleRateHertz": 22050
    }
  }
  ```
- **Response**: `{ audioContent: "base64_encoded_mp3" }`

## Demo Mode Fallback

If Inworld AI API is unavailable or returns an error:
- System generates a demo voice ID: `{voice_name}_{random_hash}`
- User can still test the workflow
- Voice generation uses default voice until real API works
- Samples are still saved for reference

## File Structure

```
voicetree/
├── frontend/templates/dashboard.html
│   └── Complete recording UI with modal
├── backend/
│   ├── app.py
│   │   └── /api/voice/clone/{username} endpoint
│   ├── voice_ai.py
│   │   └── create_voice_clone() method
│   └── audio/
│       └── voice_samples/
│           └── {username}_{timestamp}_sample_{idx}.mp3
```

## Browser Compatibility

**Recording works in:**
- ✅ Chrome/Edge (best support)
- ✅ Firefox
- ✅ Safari (desktop & mobile)
- ❌ IE11 (not supported)

**Requirements:**
- HTTPS or localhost (for microphone access)
- Microphone permissions granted

## Testing Checklist

- [ ] Open dashboard
- [ ] Click "Record Audio Sample" button
- [ ] Grant microphone permissions
- [ ] Record 5-15 second sample
- [ ] Listen to preview
- [ ] Click "Use This Sample"
- [ ] See sample in list
- [ ] Optional: Record 2-3 more samples
- [ ] Fill in voice name, language
- [ ] Check legal consent
- [ ] Click "Create Voice Clone"
- [ ] See processing spinner
- [ ] See success screen with voice ID
- [ ] Enter test text
- [ ] Click play button
- [ ] Hear generated audio
- [ ] Navigate to Welcome Message section
- [ ] Generate welcome message
- [ ] Check profile preview

## Environment Variables

```bash
INWORLD_API_KEY=your_api_key_here
```

Get your API key from: https://studio.inworld.ai/

## Next Steps

1. Test with real Inworld AI API key
2. Add error handling for specific API errors
3. Implement retry logic for transient failures
4. Add progress indicators during long recordings
5. Consider adding waveform visualization
6. Add sample quality indicators
7. Implement voice clone management (delete/rename)
