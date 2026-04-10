# Campus++ Testing Guide (Start to End)

This document gives a complete testing flow for the Campus++ AI voice calling backend.

## 1. Prerequisites

- Python 3.10+ installed
- `pip` installed
- Twilio account and phone number (for real call testing)
- ngrok installed (for Twilio webhook testing from local machine)

## 2. Setup

1. Open terminal in `ai_call_backend`.
2. Install dependencies:
   ```bash
   pip install -r requirements.
   ```
3. Create env file:
   ```bash
   copy .env.example .env
   ```
4. Fill `.env`:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_PHONE_NUMBER`
   - `MISTRAL_API_KEY` (optional; leave empty for rule-based summary)

## 3. Start Backend

Run:

```bash
uvicorn app:app --reload --port 8000
```

Expected result:
- Server starts on `http://127.0.0.1:8000`
- No import/runtime errors in terminal

## 4. API Test Cases (Local)

Use a new terminal for curl commands.

### 4.1 Health Check

- Endpoint: `GET /`
- Full URL: `http://localhost:8000/`
- Body: none

Command:

```bash
curl http://localhost:8000/
```

Expected response:
- Status: `200 OK`
- JSON:
  ```json
  {
    "status": "ok",
    "service": "Campus++ AI Voice Backend",
    "version": "1.0.0"
  }
  ```

### 4.2 Start Voice Flow

- Endpoint: `POST /api/call/voice`
- Full URL: `http://localhost:8000/api/call/voice`
- Body: none (`application/x-www-form-urlencoded` not required here)

Command:

```bash
curl -X POST http://localhost:8000/api/call/voice
```

Expected response:
- Status: `200 OK`
- Content-Type: `application/xml`
- TwiML includes:
  - Welcome message
  - `<Gather ... action="/api/call/process-id" ...>`
  - Fallback redirect to `/api/call/voice`

### 4.3 Submit Student ID

- Endpoint: `POST /api/call/process-id`
- Full URL: `http://localhost:8000/api/call/process-id`
- Body type: `application/x-www-form-urlencoded`
- Body:
  - `Digits=1234`

Command:

```bash
curl -X POST http://localhost:8000/api/call/process-id -d "Digits=1234"
```

Expected response:
- Status: `200 OK`
- Content-Type: `application/xml`
- TwiML includes:
  - Confirmation of entered student ID
  - `<Gather ... action="/api/call/process-pin?student_id=1234" ...>`
  - Prompt asking for 4-digit PIN

### 4.4 Submit PIN (Happy Path)

- Endpoint: `POST /api/call/process-pin`
- Full URL: `http://localhost:8000/api/call/process-pin?student_id=1234`
- Body type: `application/x-www-form-urlencoded`
- Body:
  - `Digits=1234`

Command:

```bash
curl -X POST "http://localhost:8000/api/call/process-pin?student_id=1234" -d "Digits=1234"
```

Expected response:
- Status: `200 OK`
- Content-Type: `application/xml`
- TwiML includes:
  - Verification success message
  - AI/rule-based performance summary
  - Closing message
  - `<Hangup/>`

## 5. Negative Test Cases

### 5.1 Missing Student ID

- Endpoint: `POST /api/call/process-id`
- Body: empty `Digits`

Command:

```bash
curl -X POST http://localhost:8000/api/call/process-id -d "Digits="
```

Expected response:
- TwiML says no student ID entered
- Redirect to `/api/call/voice`

### 5.2 Unknown Student ID

- Endpoint: `POST /api/call/process-pin`
- URL: `http://localhost:8000/api/call/process-pin?student_id=1111`
- Body: `Digits=1234`

Command:

```bash
curl -X POST "http://localhost:8000/api/call/process-pin?student_id=1111" -d "Digits=1234"
```

Expected response:
- TwiML says student not found
- Call ends with `<Hangup/>`

### 5.3 Wrong PIN

- Endpoint: `POST /api/call/process-pin`
- URL: `http://localhost:8000/api/call/process-pin?student_id=1234`
- Body: `Digits=0000`

Command:

```bash
curl -X POST "http://localhost:8000/api/call/process-pin?student_id=1234" -d "Digits=0000"
```

Expected response:
- TwiML says PIN is incorrect
- Call ends with `<Hangup/>`

### 5.4 Missing PIN

- Endpoint: `POST /api/call/process-pin`
- URL: `http://localhost:8000/api/call/process-pin?student_id=1234`
- Body: empty `Digits`

Command:

```bash
curl -X POST "http://localhost:8000/api/call/process-pin?student_id=1234" -d "Digits="
```

Expected response:
- TwiML says could not verify details
- Call ends with `<Hangup/>`

## 6. End-to-End Real Call Test (Twilio)

1. Start backend:
   ```bash
   uvicorn app:app --reload --port 8000
   ```
2. Start ngrok:
   ```bash
   ngrok http 8000
   ```
3. Copy HTTPS ngrok URL, example:
   - `https://abcd-1234.ngrok-free.app`
4. In Twilio Console for your number:
   - Voice webhook URL: `https://abcd-1234.ngrok-free.app/api/call/voice`
   - Method: `POST`
5. Call the Twilio number from any phone.
6. Enter:
   - Student ID: `1234#`
   - PIN: `1234#`

Expected call behavior:
- Greeting in Indian English voice
- Prompt for student ID
- Prompt for verification PIN
- Spoken personalized Hinglish summary
- Closing line and call hangup

## 7. Demo Credentials

- Student ID: `1234`
- PIN: `1234`

## 8. Troubleshooting

- `422 Unprocessable Entity`:
  - Ensure requests use form body `Digits=...`, not JSON.
- Twilio says webhook failed:
  - Confirm ngrok URL is active and uses HTTPS.
  - Confirm webhook path is exactly `/api/call/voice`.
- No AI-style response:
  - Add valid `MISTRAL_API_KEY` in `.env`, or use fallback behavior.
- Import or runtime issues:
  - Reinstall dependencies with `pip install -r requirements.txt`.
