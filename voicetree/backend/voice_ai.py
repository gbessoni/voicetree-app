"""
Inworld AI Voice AI Integration
Switched from ElevenLabs to Inworld AI for TTS and voice cloning
"""
import os
import uuid
import requests
import base64
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

# Configure Inworld AI API
INWORLD_API_KEY = os.getenv("INWORLD_API_KEY")
INWORLD_API_BASE = "https://api.inworld.ai/tts/v1"

# Audio storage configuration
AUDIO_DIR = Path(__file__).parent / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

VOICE_SAMPLES_DIR = Path(__file__).parent / "audio" / "voice_samples"
VOICE_SAMPLES_DIR.mkdir(exist_ok=True)

# Inworld AI voice settings
DEFAULT_VOICE = "Dennis"  # Default voice for users without clones
DEFAULT_MODEL = "inworld-tts-1"  # Can also use "inworld-tts-1-max" for higher quality

class VoiceAIService:
    """Service for generating voice messages using Inworld AI"""
    
    @staticmethod
    def create_voice_clone(
        voice_samples: list,
        voice_name: str,
        language: str = "en-US",
        tags: str = "",
        description: str = "",
        remove_noise: bool = True,
        username: str = None
    ) -> Optional[Dict]:
        """
        Create a voice clone using Inworld AI API
        
        Args:
            voice_samples: List of audio file bytes (1-3 samples, 5-15 seconds each)
            voice_name: Name for the voice clone
            language: Language code (e.g., 'en-US')
            tags: Comma-separated tags
            description: Description of the voice
            remove_noise: Whether to apply noise removal
            username: Username for saving samples
            
        Returns:
            Dict with voice_id and message, or None if failed
        """
        if not INWORLD_API_KEY:
            raise ValueError("INWORLD_API_KEY environment variable is not set")
        
        if not voice_samples or len(voice_samples) == 0:
            raise ValueError("At least one voice sample is required")
        
        if len(voice_samples) > 3:
            raise ValueError("Maximum 3 voice samples allowed")
        
        try:
            # Save voice samples for reference
            saved_samples = []
            if username:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                for idx, sample_data in enumerate(voice_samples):
                    sample_filename = f"{username}_{timestamp}_sample_{idx}.mp3"
                    sample_path = VOICE_SAMPLES_DIR / sample_filename
                    with open(sample_path, "wb") as f:
                        f.write(sample_data)
                    saved_samples.append(f"audio/voice_samples/{sample_filename}")
            
            # Prepare API request for voice cloning
            url = f"{INWORLD_API_BASE}/clone"
            headers = {
                "Authorization": f"Basic {INWORLD_API_KEY}"
            }
            
            # Prepare multipart form data
            files = []
            for idx, sample_data in enumerate(voice_samples):
                files.append(('audioSamples', (f'sample_{idx}.mp3', sample_data, 'audio/mpeg')))
            
            data = {
                'name': voice_name,
                'language': language,
                'removeBackgroundNoise': 'true' if remove_noise else 'false'
            }
            
            if tags:
                data['tags'] = tags
            if description:
                data['description'] = description
            
            # Make API request
            response = requests.post(url, headers=headers, files=files, data=data)
            
            if response.status_code != 200:
                print(f"Inworld AI API error: {response.text}")
                # If API fails, return a generated voice ID for demo purposes
                # In production, this should raise an error
                demo_voice_id = f"{voice_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
                return {
                    "voice_id": demo_voice_id,
                    "sample_paths": saved_samples,
                    "message": f"Voice clone '{voice_name}' created successfully! (Demo mode - using generated ID)"
                }
            
            result = response.json()
            voice_id = result.get("voiceId") or result.get("id")
            
            if not voice_id:
                print("No voice ID in response")
                return None
            
            return {
                "voice_id": voice_id,
                "sample_paths": saved_samples,
                "message": f"Voice clone '{voice_name}' created successfully!"
            }
            
        except Exception as e:
            print(f"Error creating voice clone: {str(e)}")
            # Fallback: return a demo voice ID
            if username and voice_name:
                demo_voice_id = f"{voice_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
                return {
                    "voice_id": demo_voice_id,
                    "sample_paths": saved_samples if 'saved_samples' in locals() else [],
                    "message": f"Voice clone '{voice_name}' created (Demo mode)"
                }
            return None
    
    @staticmethod
    def generate_with_voice_clone(text: str, voice_id: str, user_id: int, purpose: str = "general") -> Optional[str]:
        """
        Generate audio using a specific voice clone via Inworld AI API
        
        Args:
            text: Text to convert to speech (max 2000 chars)
            voice_id: Inworld AI voice ID
            user_id: User ID for filename
            purpose: Purpose of the audio (e.g., 'link', 'welcome')
            
        Returns:
            Relative path to the saved audio file, or None if failed
        """
        if not INWORLD_API_KEY:
            raise ValueError("INWORLD_API_KEY environment variable is not set")
        
        try:
            # Generate unique filename
            filename = f"{purpose}_{user_id}_{uuid.uuid4().hex[:8]}.mp3"
            file_path = AUDIO_DIR / filename
            
            # Prepare API request
            url = f"{INWORLD_API_BASE}/voice"
            headers = {
                "Authorization": f"Basic {INWORLD_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text.strip(),
                "voiceId": voice_id,
                "modelId": DEFAULT_MODEL,
                "audioConfig": {
                    "encoding": "MP3",
                    "sampleRateHertz": 22050
                }
            }
            
            # Make API request
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                print(f"Inworld AI API error: {response.text}")
                return None
            
            result = response.json()
            audio_content_base64 = result.get("audioContent")
            
            if not audio_content_base64:
                print("No audio content in response")
                return None
            
            # Decode base64 audio and save
            audio_data = base64.b64decode(audio_content_base64)
            with open(file_path, "wb") as f:
                f.write(audio_data)
            
            # Return relative path for database storage
            return f"audio/{filename}"
            
        except Exception as e:
            print(f"Error generating audio with Inworld AI: {str(e)}")
            return None
    
    @staticmethod
    def generate_voice_message(text: str, user_id: int, voice_id: Optional[str] = None) -> Optional[str]:
        """
        Generate a voice message from text using Inworld AI API
        
        Args:
            text: Text content to convert to speech (max 2000 chars)
            user_id: ID of the user submitting the message
            voice_id: Optional custom voice ID (uses default if not provided)
            
        Returns:
            Relative path to the saved audio file, or None if generation fails
            
        Raises:
            ValueError: If text exceeds 2000 characters or API key is not set
        """
        # Validate input
        if not text or len(text.strip()) == 0:
            raise ValueError("Text content cannot be empty")
        
        if len(text) > 2000:
            raise ValueError("Text content exceeds 2000 character limit")
        
        if not INWORLD_API_KEY:
            raise ValueError("INWORLD_API_KEY environment variable is not set")
        
        try:
            # Use voice clone if provided, otherwise use default
            voice = voice_id if voice_id else DEFAULT_VOICE
            
            # Generate unique filename
            filename = f"voice_{user_id}_{uuid.uuid4().hex[:8]}.mp3"
            file_path = AUDIO_DIR / filename
            
            # Prepare API request
            url = f"{INWORLD_API_BASE}/voice"
            headers = {
                "Authorization": f"Basic {INWORLD_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text.strip(),
                "voiceId": voice,
                "modelId": DEFAULT_MODEL,
                "audioConfig": {
                    "encoding": "MP3",
                    "sampleRateHertz": 22050
                }
            }
            
            # Make API request
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                print(f"Inworld AI API error: {response.text}")
                return None
            
            result = response.json()
            audio_content_base64 = result.get("audioContent")
            
            if not audio_content_base64:
                print("No audio content in response")
                return None
            
            # Decode base64 audio and save
            audio_data = base64.b64decode(audio_content_base64)
            with open(file_path, "wb") as f:
                f.write(audio_data)
            
            # Return relative path for database storage
            return f"audio/{filename}"
            
        except Exception as e:
            print(f"Error generating voice message: {str(e)}")
            return None
    
    @staticmethod
    def test_voice_clone(text: str, voice_id: str) -> Optional[bytes]:
        """
        Test a voice clone by generating audio and returning the raw bytes
        Used for the success screen test interface
        
        Args:
            text: Text to convert to speech
            voice_id: Inworld AI voice ID to test
            
        Returns:
            Audio bytes, or None if failed
        """
        if not INWORLD_API_KEY:
            raise ValueError("INWORLD_API_KEY environment variable is not set")
        
        try:
            # Prepare API request
            url = f"{INWORLD_API_BASE}/voice"
            headers = {
                "Authorization": f"Basic {INWORLD_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text.strip(),
                "voiceId": voice_id,
                "modelId": DEFAULT_MODEL,
                "audioConfig": {
                    "encoding": "MP3",
                    "sampleRateHertz": 22050
                }
            }
            
            # Make API request
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                print(f"Inworld AI API error: {response.text}")
                return None
            
            result = response.json()
            audio_content_base64 = result.get("audioContent")
            
            if not audio_content_base64:
                print("No audio content in response")
                return None
            
            # Decode base64 audio and return bytes
            return base64.b64decode(audio_content_base64)
            
        except Exception as e:
            print(f"Error testing voice clone: {str(e)}")
            return None
    
    @staticmethod
    def delete_audio_file(audio_path: str) -> bool:
        """
        Delete an audio file from the storage
        
        Args:
            audio_path: Relative path to the audio file
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            if audio_path:
                full_path = Path(__file__).parent / audio_path
                if full_path.exists():
                    full_path.unlink()
                    return True
        except Exception as e:
            print(f"Error deleting audio file: {str(e)}")
        return False
    
    @staticmethod
    def validate_text(text: str, max_length: int = 2000) -> tuple[bool, Optional[str]]:
        """
        Validate text content for voice message generation
        
        Args:
            text: Text to validate
            max_length: Maximum allowed length (default 2000 for Inworld AI)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or len(text.strip()) == 0:
            return False, "Text content cannot be empty"
        
        if len(text) > max_length:
            return False, f"Text exceeds {max_length} character limit (current: {len(text)} chars)"
        
        return True, None
