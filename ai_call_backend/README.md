# Campus++ - AI Voice Calling Backend

An AI-powered phone-call assistant for college students who do not have smartphones or reliable internet.
Students call a normal phone number, verify with keypad input, and hear a personalized Hinglish academic summary.

## One-liner
Campus++ lets students call and hear attendance, marks, quiz average, risk level, and improvement tips without an app.

## Problem
Many tier-2 and tier-3 college students in India are excluded from app-based academic systems due to device and connectivity limitations.

## Solution
Call flow:
1. Student calls Twilio number.
2. Student enters Student ID using DTMF keypad.
3. Student enters 4-digit verification PIN.
4. Backend fetches student data.
5. LangGraph + Mistral (or rule-based fallback) generates a Hinglish summary.
6. Twilio reads it in `Polly.Aditi` voice and ends the call.

## Tech Stack
- FastAPI (Python backend)
- Twilio Voice + TwiML
- LangGraph orchestration
- Mistral LLM (`langchain-mistralai`)
- Mock data layer (MongoDB-ready)
- AWS Polly Aditi voice via Twilio (`en-IN`)

## Project Structure
```text
ai_call_backend/
|-- app.py
|-- requirements.txt
|-- .env.example
|-- routes/
|   |-- call.py
|-- services/
|   |-- ai_agent.py
|   |-- student_service.py
```

## API Endpoints
- `POST /api/call/voice`: Welcome and gather Student ID
- `POST /api/call/process-id`: Gather verification PIN
- `POST /api/call/process-pin`: Verify + generate summary + hangup

## Quick Start
```bash
cd ai_call_backend
pip install -r requirements.txt
copy .env.example .env
uvicorn app:app --reload --port 8000
```

## Local Testing
```bash
curl http://localhost:8000/
curl -X POST http://localhost:8000/api/call/voice
curl -X POST http://localhost:8000/api/call/process-id -d "Digits=1234"
curl -X POST "http://localhost:8000/api/call/process-pin?student_id=1234" -d "Digits=1234"
```

## Twilio Setup
1. Start ngrok:
   ```bash
   ngrok http 8000
   ```
2. Set Twilio voice webhook to:
   ```text
   https://YOUR_NGROK_URL/api/call/voice
   ```
3. Call your Twilio number.

## Demo Credentials (for judges)
- Student ID: `1234`
- Verification PIN: `1234`

## Notes
- If `MISTRAL_API_KEY` is empty, the backend uses a deterministic rule-based summary generator.
- Replace `MOCK_STUDENTS` in `services/student_service.py` with MongoDB queries for production.

## Testing
- Full end-to-end testing steps are in `TESTING.md`.
