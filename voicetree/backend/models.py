"""
Database Models for VoiceTree
GitHub Issue #1: User profile model and link management
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    """User profile model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_published = Column(Boolean, default=False)
    imported_from_linktree = Column(Boolean, default=False)
    
    # Voice AI fields
    voice_clone_id = Column(String(100), nullable=True)  # ElevenLabs voice ID
    voice_sample_path = Column(String(500), nullable=True)  # Path to uploaded voice sample
    welcome_message_text = Column(Text, nullable=True)  # Welcome message text
    welcome_message_audio = Column(String(500), nullable=True)  # Path to welcome audio
    welcome_message_type = Column(String(20), default="static")  # "static" or "daily_ai"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to links
    links = relationship("Link", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(username='{self.username}', display_name='{self.display_name}')>"

class Link(Base):
    """Link model for user's links"""
    __tablename__ = "links"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    url = Column(String(1000), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    
    # Voice message fields for per-link intros
    voice_message_text = Column(String(200), nullable=True)  # Max 50 words (~200 chars)
    voice_message_audio = Column(String(500), nullable=True)  # Path to audio file
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to user
    user = relationship("User", back_populates="links")
    
    def __repr__(self):
        return f"<Link(title='{self.title}', url='{self.url}')>"

class VoiceMessage(Base):
    """Voice message model with ElevenLabs AI integration - GitHub Issue #2"""
    __tablename__ = "voice_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text_content = Column(String(500), nullable=False)  # Max 500 characters
    audio_file_path = Column(String(500), nullable=True)  # Path to generated audio
    is_approved = Column(Boolean, default=False)  # Admin approval status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship to user
    user = relationship("User", backref="voice_messages")
    
    def __repr__(self):
        return f"<VoiceMessage(user_id={self.user_id}, approved={self.is_approved})>"
