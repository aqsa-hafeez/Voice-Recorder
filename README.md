# Backend — Voice Conversation Recorder

FastAPI backend that takes an audio file, produces a speaker-diarized
transcript using ElevenLabs Scribe v2, and saves everything to a database
(audio, transcript, and title are all saved permanently).

## Live Deployment

| Part | URL |
|---|---|
| Frontend (share this with the client) | https://voice-recording.lovable.app |
| Backend API (internal only — called by Lovable) | https://voice-recorder-6y3y.vercel.app |
| Database | Supabase Postgres (free tier) |

⚠️ Supabase free tier: if the database sees **zero activity for 7 days**
(no upload/history requests), the project automatically pauses. Data is
not deleted — a single click on "Restore" in the Supabase dashboard brings
it back. With regular use this will never be an issue.

ℹ️ This app has no login/authentication — whoever opens the frontend link
sees the same shared history (there is no per-user private data). This is
intentional for the current use case.

## Local Setup

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the .env file
cp .env.example .env
# Open .env and replace ELEVENLABS_API_KEY with your own key
# (get one by creating an account at elevenlabs.io)
# For local testing, leave the default SQLite line as is

# 4. Run the server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once the server is running, go to `http://localhost:8000/docs` to test every
endpoint via the Swagger UI (you can even upload a file directly from there).

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Health check |
| POST | `/api/upload` | Upload audio → transcription → save to DB (audio is saved too) |
| GET | `/api/conversations` | List of all conversations (history) |
| GET | `/api/conversations/{id}` | Full speaker-wise transcript for one conversation |
| GET | `/api/conversations/{id}/audio` | The saved recording's audio (for playback) |
| PATCH | `/api/conversations/{id}` | Rename a recording's title |
| DELETE | `/api/conversations/{id}` | Delete a conversation |

`POST /api/upload` form fields:
- `file` (required) — the audio file
- `language_code` (optional) — only `"en"` or `"ur"` are allowed; defaults to `"ur"` if not sent
- `title` (optional) — a custom title; auto-generated if not sent

## Testing with curl

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

## Persistent Database (Production)

Vercel's serverless filesystem is **temporary** — if SQLite were used, the
file (`/tmp/storage/app.db`) could be wiped at any time (a new cold start, a
redeploy, etc.), taking all history, titles, and audio with it. Because of
this, the production backend now runs on **Supabase Postgres** (free tier),
configured via the `DATABASE_URL` environment variable in Vercel
(Settings → Environment Variables).

If you ever need to migrate to a different Postgres provider (e.g. Neon):
1. Get a connection string from the new provider (format: `postgresql://user:password@host/dbname?sslmode=require`)
2. Update `DATABASE_URL` in Vercel → Settings → Environment Variables
3. Redeploy

Existing data will not migrate automatically — the new database will start empty.

## Testing Locally from a Phone

If you ever need to test the local backend from a phone (not needed in
production, since the Vercel URL is already public):
- Both devices must be on the same WiFi network; use the backend's local IP
  (e.g. `http://192.168.1.5:8000`) — `localhost` won't work from a phone
- Or use a tool like `ngrok` to create a temporary public URL for testing
