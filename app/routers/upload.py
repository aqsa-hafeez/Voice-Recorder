import os
import uuid
from datetime import datetime

from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db, Conversation, Segment
from app.models.schemas import ConversationOut, ConversationDetailOut, ConversationUpdate
from app.services.elevenlabs_service import transcribe_with_diarization

router = APIRouter(prefix="/api", tags=["conversations"])

# Only these two are supported. Urdu and Hindi sound alike to auto-detect,
# so we never let it fall through to Hindi - default to Urdu when the
# caller doesn't specify a language.
ALLOWED_LANGUAGES = {"en", "ur"}
DEFAULT_LANGUAGE = "ur"

EXT_TO_MIME = {
    ".webm": "audio/webm",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".mp4": "audio/mp4",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
}


@router.post("/upload", response_model=ConversationDetailOut)
async def upload_audio(
    file: UploadFile = File(...),
    language_code: Optional[str] = Form(
        None,
        description="'en' for English or 'ur' for Urdu. Defaults to 'ur' if not sent.",
    ),
    title: Optional[str] = Form(
        None,
        description="Optional custom title. Auto-generated if not sent.",
    ),
    db: Session = Depends(get_db),
):
    language_code = language_code.strip().lower() if language_code and language_code.strip() else DEFAULT_LANGUAGE
    if language_code not in ALLOWED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"language_code must be one of {sorted(ALLOWED_LANGUAGES)}, got '{language_code}'",
        )

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file mila")

    ext = os.path.splitext(file.filename or "audio.m4a")[1].lower() or ".m4a"
    mime_type = EXT_TO_MIME.get(ext, file.content_type or "audio/webm")

    clean_title = title.strip() if title and title.strip() else f"Conversation - {datetime.now().strftime('%d %b, %I:%M %p')}"

    conversation = Conversation(
        title=clean_title,
        status="processing",
        audio_data=audio_bytes,
        audio_mime_type=mime_type,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    try:
        result = transcribe_with_diarization(
            audio_bytes,
            file.filename or f"{uuid.uuid4().hex}{ext}",
            language_code=language_code,
            num_speakers=None,  
        )
    except Exception as e:
        conversation.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=f"Transcription failed: {str(e)}")


    conversation.language_detected = result["language_code"]
    conversation.duration_sec = result["duration_sec"]
    conversation.status = "done"

    for seg in result["segments"]:
        db.add(Segment(
            conversation_id=conversation.id,
            speaker_label=seg["speaker_label"],
            text=seg["text"],
            start_time=seg["start_time"],
            end_time=seg["end_time"],
        ))

    db.commit()
    db.refresh(conversation)

    return conversation


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db)):
    """History screen ke liye - saari conversations, newest pehle."""
    return (
        db.query(Conversation)
        .order_by(Conversation.created_at.desc())
        .all()
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailOut)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Detail screen ke liye - ek conversation ka poora speaker-wise transcript."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation nahi mili")
    return conversation


@router.get("/conversations/{conversation_id}/audio")
def get_conversation_audio(conversation_id: int, db: Session = Depends(get_db)):
    """Saved recording ki audio wapas bhejta hai (playback ke liye)."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation nahi mili")
    if not conversation.audio_data:
        raise HTTPException(status_code=404, detail="Is conversation ke liye audio save nahi hai")
    return Response(
        content=conversation.audio_data,
        media_type=conversation.audio_mime_type or "audio/webm",
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationDetailOut)
def rename_conversation(
    conversation_id: int,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
):
    """Recording ka title update/rename karta hai."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation nahi mili")
    clean_title = payload.title.strip()
    if not clean_title:
        raise HTTPException(status_code=400, detail="Title khali nahi ho sakta")
    conversation.title = clean_title
    db.commit()
    db.refresh(conversation)
    return conversation


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation nahi mili")
    db.delete(conversation)
    db.commit()
    return {"message": "Delete ho gaya"}
