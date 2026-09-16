from io import BytesIO
from typing import List, Dict, Any

from elevenlabs.client import ElevenLabs

from app.core.config import settings

client = ElevenLabs(api_key=settings.elevenlabs_api_key)


def transcribe_with_diarization(
    audio_bytes: bytes,
    filename: str,
    language_code: str = None,
    num_speakers: int = None,
) -> Dict[str, Any]:
    """
    Audio bytes ko ElevenLabs Scribe v2 ko bhejta hai.

    language_code: "en" for English or "ur" for Urdu. The /api/upload route
        always passes one of these explicitly (defaulting to "ur") because
        auto-detect confuses Urdu with Hindi and returns the wrong script.

    num_speakers: agar pata hai kitne log bol rahay hain (e.g. 2), to pass karein.
        Ye auto-detect (None) se zyada reliable hota hai.

    Returns: {
        "language_code": str,
        "duration_sec": float,
        "segments": [{"speaker_label": str, "text": str, "start_time": float, "end_time": float}, ...]
    }
    """
    audio_file = BytesIO(audio_bytes)
    audio_file.name = filename

    result = client.speech_to_text.convert(
        file=audio_file,
        model_id="scribe_v2",
        diarize=True,                  
        num_speakers=num_speakers,       
        language_code=language_code,    
        tag_audio_events=False,
    )

    words = result.words or []
    segments = _merge_words_into_segments(words)

    duration_sec = words[-1].end if words else 0.0

    return {
        "language_code": getattr(result, "language_code", None),
        "duration_sec": duration_sec,
        "segments": segments,
    }


def _merge_words_into_segments(words: List[Any]) -> List[Dict[str, Any]]:
    """
    Word-by-word output ko speaker-wise merged segments mein convert karta hai.
    Jab tak speaker same rahay, words ko ek segment mein jorte jao.
    Speaker change hote hi naya segment shuru.
    """
    segments: List[Dict[str, Any]] = []
    current_speaker = None
    current_text_parts: List[str] = []
    current_start = None
    current_end = None

    for word in words:
        if getattr(word, "type", "word") != "word":
            continue

        speaker = getattr(word, "speaker_id", "speaker_1") or "speaker_1"

        if speaker != current_speaker:
            if current_speaker is not None:
                segments.append({
                    "speaker_label": current_speaker,
                    "text": " ".join(current_text_parts).strip(),
                    "start_time": current_start,
                    "end_time": current_end,
                })
            current_speaker = speaker
            current_text_parts = [word.text]
            current_start = word.start
            current_end = word.end
        else:
            current_text_parts.append(word.text)
            current_end = word.end

    if current_speaker is not None:
        segments.append({
            "speaker_label": current_speaker,
            "text": " ".join(current_text_parts).strip(),
            "start_time": current_start,
            "end_time": current_end,
        })

    return segments
