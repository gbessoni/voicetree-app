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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to links
    links = relationship("Link", back_populates="user", cascade="all, delete-orphan")
    voice_bio = relationship("VoiceBio", uselist=False, back_populates="user", cascade="all, delete-orphan")
    
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to user
    user = relationship("User", back_populates="links")
    
    def __repr__(self):
        return f"<Link(title='{self.title}', url='{self.url}')>"

class VoiceBio(Base):
    """Voice bio model"""
    __tablename__ = "voice_bios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    text = Column(Text, nullable=False)
    audio_url = Column(String(500), nullable=True)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to user
    user = relationship("User", back_populates="voice_bio")

    def __repr__(self):
        return f"<VoiceBio(user_id='{self.user_id}', is_approved='{self.is_approved}')>"
