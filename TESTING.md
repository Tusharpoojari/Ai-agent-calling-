# Campus++ Testing Guide (Student ID Only Flow)

This guide matches the current backend flow:
1. Caller enters Student ID
2. System fetches data and speaks summary
3. Call ends

## 1. Start Server

From project root:

```powershell
uvicorn app:app --reload --port 8000
```

Expected:
- Server runs at `http://127.0.0.1:8000`

## 2. API Tests (PowerShell)

### 2.1 Health

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/"
```

Expected:
- `200 OK`
- JSON health response

### 2.2 Voice Entry

```powershell
(Invoke-WebRequest -Method POST -Uri "http://localhost:8000/api/call/voice").Content
```

Expected TwiML:
- Welcome message
- `Gather` with `action="/api/call/process-id"`

### 2.3 Student ID Only (Happy Path)

```powershell
(Invoke-WebRequest -Method POST -Uri "http://localhost:8000/api/call/process-id" -Body @{ Digits = "1234" }).Content
```

Expected TwiML:
- Confirms student ID
- Says it is analyzing performance
- Speaks personalized summary
- Closing message
- `<Hangup />`

### 2.4 Unknown Student ID

```powershell
(Invoke-WebRequest -Method POST -Uri "http://localhost:8000/api/call/process-id" -Body @{ Digits = "1111" }).Content
```

Expected TwiML:
- Student not found message
- `<Hangup />`

### 2.5 Missing Student ID

```powershell
(Invoke-WebRequest -Method POST -Uri "http://localhost:8000/api/call/process-id" -Body @{ Digits = "" }).Content
```

Expected TwiML:
- "No student ID was entered"
- Redirect back to `/api/call/voice`

## 3. Render Testing

If hosted on Render at `https://ai-agent-calling.onrender.com`:

```powershell
(Invoke-WebRequest -Method POST -Uri "https://ai-agent-calling.onrender.com/api/call/voice").Content
(Invoke-WebRequest -Method POST -Uri "https://ai-agent-calling.onrender.com/api/call/process-id" -Body @{ Digits = "1234" }).Content
```

Expected:
- First call returns gather for student ID
- Second call returns summary and hangup

## 4. Twilio Real Call Test

1. In Twilio number settings, set voice webhook:
   - URL: `https://ai-agent-calling.onrender.com/api/call/voice`
   - Method: `POST`
2. Call your Twilio number.
3. Enter Student ID: `1234#`.

Expected call behavior:
- Welcome prompt
- Ask for Student ID
- Summary is spoken
- Goodbye message
- Call ends

## 5. Demo Credential

- Student ID: `1234`
