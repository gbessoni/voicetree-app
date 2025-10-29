# crud.py
from sqlalchemy.orm import Session
from models import User, Link, VoiceBio
from schemas import UserCreate, LinkCreate, VoiceBioCreate

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
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

def create_user_link(db: Session, link: LinkCreate, user_id: int):
    db_link = Link(**link.dict(), user_id=user_id)
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

def get_user_links(db: Session, user_id: int):
    return db.query(Link).filter(Link.user_id == user_id, Link.is_active == True).all()

def create_or_update_voice_bio(db: Session, voice_bio: VoiceBioCreate, user_id: int):
    db_voice_bio = db.query(VoiceBio).filter(VoiceBio.user_id == user_id).first()
    if db_voice_bio:
        db_voice_bio.text = voice_bio.text
        db_voice_bio.is_approved = False
    else:
        db_voice_bio = VoiceBio(
            user_id=user_id,
            text=voice_bio.text
        )
        db.add(db_voice_bio)
    db.commit()
    db.refresh(db_voice_bio)
    return db_voice_bio

def get_approved_voice_bio(db: Session, user_id: int):
    return db.query(VoiceBio).filter(VoiceBio.user_id == user_id, VoiceBio.is_approved == True).first()

def get_unapproved_voice_bios(db: Session):
    return db.query(VoiceBio).filter(VoiceBio.is_approved == False).all()

def approve_voice_bio(db: Session, voice_bio_id: int):
    voice_bio = db.query(VoiceBio).filter(VoiceBio.id == voice_bio_id).first()
    if voice_bio:
        voice_bio.is_approved = True
        db.commit()
    return voice_bio

def reject_voice_bio(db: Session, voice_bio_id: int):
    voice_bio = db.query(VoiceBio).filter(VoiceBio.id == voice_bio_id).first()
    if voice_bio:
        db.delete(voice_bio)
        db.commit()
    return voice_bio
