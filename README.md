# Backend — Voice Conversation Recorder

FastAPI backend jo audio file leta hai, ElevenLabs Scribe v2 se speaker-diarized
transcript banata hai, aur SQLite mein save karta hai.

## Setup

```bash
# 1. Virtual environment banayein
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Dependencies install karein
pip install -r requirements.txt

# 3. .env file banayein
cp .env.example .env
# .env kholein aur ELEVENLABS_API_KEY apni key se replace karein
# (key elevenlabs.io par account bana kar milegi)

# 4. Server run karein
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Server chalne ke baad: `http://localhost:8000/docs` par jaa kar Swagger UI
mein saare endpoints test kar sakte hain (file upload bhi wahin se ho sakta hai).

## Endpoints

| Method | Endpoint | Kaam |
|---|---|---|
| GET | `/` | Health check |
| POST | `/api/upload` | Audio upload → transcription → DB save (audio bhi save hota hai) |
| GET | `/api/conversations` | Saari conversations ki list (history) |
| GET | `/api/conversations/{id}` | Ek conversation ka poora speaker-wise transcript |
| GET | `/api/conversations/{id}/audio` | Saved recording ki audio (playback ke liye) |
| PATCH | `/api/conversations/{id}` | Recording ka title rename karna |
| DELETE | `/api/conversations/{id}` | Conversation delete karna |

`POST /api/upload` ke form fields:
- `file` (required) — audio file
- `language_code` (optional) — sirf `"en"` ya `"ur"` allowed; na diya to `"ur"` default hota hai
- `title` (optional) — custom title; na diya to auto-generate hota hai

## Testing (curl se)

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@sample_audio.mp3" \
  -F "language_code=ur" \
  -F "title=Meeting with Ali"

curl "http://localhost:8000/api/conversations/1/audio" --output playback.webm

curl -X PATCH "http://localhost:8000/api/conversations/1" \
  -H "Content-Type: application/json" \
  -d '{"title": "New title"}'
```

## ⚠️ Production par persistent database zaroori hai

Vercel serverless deployment ka filesystem **temporary** hota hai — SQLite file
(`/tmp/storage/app.db`) kabhi bhi wipe ho sakti hai (naya cold start, redeploy,
waghera), jis se saari history, titles, aur audio ek dum ghayab ho jayenge.

Isliye production ke liye ek **free Postgres database** banayein:
- [Neon](https://neon.tech) ya [Supabase](https://supabase.com) — dono free tier dete hain
- Wahan se connection string copy karein (kuch is tarah dikhegi:
  `postgresql://user:password@host/dbname?sslmode=require`)
- Vercel project → Settings → Environment Variables → `DATABASE_URL` ko
  is connection string se update karein
- Redeploy karein

Is se pehle jo bhi data SQLite mein tha wo migrate nahi hoga (kyunki wo already
temporary tha) — bas ab se sab kuch permanently save hoga.

## Phone se Test Karna

Jab Flutter app banayenge, backend ko phone se connect karne ke liye:
- Same WiFi network par ho dono devices, aur backend ka local IP use karein
  (e.g. `http://192.168.1.5:8000`) — `localhost` phone se kaam nahi karega
- Ya `ngrok` jaisa tool use kar ke temporary public URL bana lein testing ke liye
