"""
call.py - Twilio Voice Webhook Routes
=====================================
Handles the entire phone-call lifecycle:
  1. /voice        -> greets the caller, asks for student ID
  2. /process-id   -> captures keypad PIN, fetches student data, speaks a short summary
"""

import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import Gather, VoiceResponse

from services.student_service import build_student_feedback, get_student

logger = logging.getLogger("campus++.routes.call")
router = APIRouter()

# Twilio voice settings
VOICE = "Polly.Aditi"      # Indian English voice via Twilio Polly
LANGUAGE = "en-IN"
GATHER_TIMEOUT = 10
MAX_DIGITS_ID = 4


def _twiml(response: VoiceResponse) -> Response:
    """Return TwiML XML response."""
    return Response(content=str(response), media_type="application/xml")


@router.post("/voice")
async def voice_welcome(request: Request):
    """Entry webhook for incoming calls. Ask for student ID."""
    logger.info("Incoming call received")

    response = VoiceResponse()
    response.say(
        "Hello, welcome to CampusFlow.",
        voice=VOICE,
        language=LANGUAGE,
    )
    response.say(
        "This is your A I academic assistant that helps track your progress and improvement.",
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
        "Please enter your 4 digit student pin, followed by the hash key.",
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
async def process_student_id(
    request: Request,
    Digits: str = Form(""),
):
    """Capture 4-digit PIN from keypad, generate a short IVR summary, and end call."""
    student_id = "".join(ch for ch in Digits if ch.isdigit())[:MAX_DIGITS_ID]
    logger.info("Received student PIN digits: %s", student_id)

    response = VoiceResponse()

    if not student_id:
        response.say(
            "No PIN was entered. Please try again.",
            voice=VOICE,
            language=LANGUAGE,
        )
        response.redirect("/api/call/voice", method="POST")
        return _twiml(response)

    student = get_student(student_id)

    if student is None:
        response.say(
            "Sorry, that pin is not found in our records. Please check and try again.",
            voice=VOICE,
            language=LANGUAGE,
        )
        response.hangup()
        return _twiml(response)

    try:
        ivr_feedback = build_student_feedback(student)
        logger.info("IVR feedback generated successfully")
    except Exception as exc:
        logger.error("IVR feedback generation error: %s", exc)
        ivr_feedback = (
            f"Hello {student['name']}. There has not been much improvement yet, "
            "but we can improve it. Keep going, you are improving."
        )

    response.say(ivr_feedback, voice=VOICE, language=LANGUAGE)
    response.hangup()

    logger.info("Call ended gracefully")
    return _twiml(response)
