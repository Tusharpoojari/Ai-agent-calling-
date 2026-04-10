"""
call.py - Twilio Voice Webhook Routes
=====================================
Handles the entire phone-call lifecycle:
  1. /voice        -> greets the caller, asks for student ID
  2. /process-id   -> captures DTMF student ID, asks for verification PIN
  3. /process-pin  -> verifies credentials, fetches AI insights, speaks them
"""

import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import Gather, VoiceResponse

from services.ai_agent import generate_student_insights
from services.student_service import format_student_data, get_student, verify_student_pin

logger = logging.getLogger("campus++.routes.call")
router = APIRouter()

# Twilio voice settings
VOICE = "Polly.Aditi"      # Indian English voice via Twilio Polly
LANGUAGE = "en-IN"
GATHER_TIMEOUT = 10
MAX_DIGITS_ID = 10
MAX_DIGITS_PIN = 4


def _twiml(response: VoiceResponse) -> Response:
    """Return TwiML XML response."""
    return Response(content=str(response), media_type="application/xml")


@router.post("/voice")
async def voice_welcome(request: Request):
    """Entry webhook for incoming calls. Ask for student ID."""
    logger.info("Incoming call received")

    response = VoiceResponse()
    response.say(
        "Welcome to Campus Plus Plus, your AI powered academic assistant.",
        voice=VOICE,
        language=LANGUAGE,
    )

    gather = Gather(
        num_digits=MAX_DIGITS_ID,
        action="/api/call/process-id",
        method="POST",
        timeout=GATHER_TIMEOUT,
        finish_on_key="#",
    )
    gather.say(
        "Please enter your student ID using the keypad, followed by the hash key.",
        voice=VOICE,
        language=LANGUAGE,
    )
    response.append(gather)

    response.say(
        "Sorry, I did not receive any input. Please try again.",
        voice=VOICE,
        language=LANGUAGE,
    )
    response.redirect("/api/call/voice", method="POST")

    return _twiml(response)


@router.post("/process-id")
async def process_student_id(request: Request, Digits: str = Form("")):
    """Capture student ID and ask for PIN."""
    student_id = Digits.strip()
    logger.info(f"Received student ID digits: {student_id}")

    response = VoiceResponse()

    if not student_id:
        response.say(
            "No student ID was entered. Let's try again.",
            voice=VOICE,
            language=LANGUAGE,
        )
        response.redirect("/api/call/voice", method="POST")
        return _twiml(response)

    response.say(
        f"You entered student ID {' '.join(student_id)}.",
        voice=VOICE,
        language=LANGUAGE,
    )

    gather = Gather(
        num_digits=MAX_DIGITS_PIN,
        action=f"/api/call/process-pin?student_id={student_id}",
        method="POST",
        timeout=GATHER_TIMEOUT,
        finish_on_key="#",
    )
    gather.say(
        "For verification, please enter your four digit PIN, followed by the hash key.",
        voice=VOICE,
        language=LANGUAGE,
    )
    response.append(gather)

    response.say(
        "No input received. Redirecting you to the beginning.",
        voice=VOICE,
        language=LANGUAGE,
    )
    response.redirect("/api/call/voice", method="POST")

    return _twiml(response)


@router.post("/process-pin")
async def process_pin(
    request: Request,
    Digits: str = Form(""),
    student_id: str = "",
):
    """Validate PIN, generate AI summary, and end call gracefully."""
    pin = Digits.strip()
    params = request.query_params
    student_id = params.get("student_id", student_id)

    logger.info(f"Verification PIN received for student_id={student_id}")

    response = VoiceResponse()

    if not student_id or not pin:
        response.say(
            "Sorry, we could not verify your details. Please call again and try once more.",
            voice=VOICE,
            language=LANGUAGE,
        )
        response.hangup()
        return _twiml(response)

    student = get_student(student_id)

    if student is None:
        response.say(
            f"Sorry, no student found with ID {' '.join(student_id)}. Please check your ID and call again.",
            voice=VOICE,
            language=LANGUAGE,
        )
        response.hangup()
        return _twiml(response)

    if not verify_student_pin(student, pin):
        response.say(
            "The PIN you entered is incorrect. Please call again and try once more.",
            voice=VOICE,
            language=LANGUAGE,
        )
        response.hangup()
        return _twiml(response)

    student_data = format_student_data(student)

    response.say(
        "Thank you for verifying. Please hold while I analyze your academic performance.",
        voice=VOICE,
        language=LANGUAGE,
    )

    try:
        ai_response = await generate_student_insights(student_data)
        logger.info("AI response generated successfully")
    except Exception as exc:
        logger.error(f"AI agent error: {exc}")
        ai_response = (
            f"Dekho, your attendance is {student['attendance']} percent, your marks average is "
            f"{student['marks']} percent, and your quiz average is {student['quizAvg']} percent. "
            f"Your current risk level is {student['riskLevel']}. Keep working hard and you will improve."
        )

    response.say(ai_response, voice=VOICE, language=LANGUAGE)
    response.say(
        "That is your personalized summary from Campus Plus Plus. Thank you, and all the best for your semester.",
        voice=VOICE,
        language=LANGUAGE,
    )
    response.hangup()

    logger.info("Call ended gracefully")
    return _twiml(response)
