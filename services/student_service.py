"""
student_service.py - Student Data Layer
=======================================
Fetches IVR student data from the CampusFlow backend and builds a
short, phone-friendly response.
"""

import json
import logging
import os
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

logger = logging.getLogger("campus++.services.student")

STUDENT_IVR_API_BASE_URL = os.getenv(
    "STUDENT_IVR_API_BASE_URL",
    "https://campuspp-f7qx.onrender.com",
).rstrip("/")


def _fetch_student_ivr_data(pin: str) -> Optional[dict]:
    """Fetch IVR-ready student data by 4-digit PIN."""
    request_url = (
        f"{STUDENT_IVR_API_BASE_URL}/api/student/public/ivr-data?pin={quote(pin)}"
    )
    request = Request(
        request_url,
        headers={"Accept": "application/json"},
        method="GET",
    )

    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            logger.warning("PIN not found in IVR backend: %s", pin)
            return None
        logger.error("IVR backend HTTP error for PIN %s: %s", pin, exc)
        return None
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.error("IVR backend lookup failed for PIN %s: %s", pin, exc)
        return None

    if not payload.get("success"):
        logger.warning("IVR backend returned unsuccessful payload for PIN: %s", pin)
        return None

    data = payload.get("data") or {}
    student_data = data.get("studentData") or {}
    metrics = data.get("metrics") or {}
    insights = data.get("insights") or {}

    return {
        "pin": pin,
        "name": student_data.get("name", "Student"),
        "student_data": student_data,
        "metrics": metrics,
        "insights": insights,
    }


def get_student(student_id: str) -> Optional[dict]:
    """Look up a student by 4-digit PIN."""
    student = _fetch_student_ivr_data(student_id)
    if student:
        logger.info(
            "Found student from IVR backend: %s (PIN: %s)",
            student["name"],
            student_id,
        )
        return student

    logger.warning("Student not found for PIN: %s", student_id)
    return None


def _pick_subject_extremes(subjects: dict) -> tuple[Optional[str], Optional[str]]:
    """Return best and weakest subject names."""
    numeric_subjects = {
        subject: score
        for subject, score in subjects.items()
        if isinstance(score, (int, float))
    }
    if not numeric_subjects:
        return None, None

    best_subject = max(numeric_subjects, key=numeric_subjects.get)
    weak_subject = min(numeric_subjects, key=numeric_subjects.get)
    return best_subject, weak_subject


def build_student_feedback(student: dict) -> str:
    """Build a short, teacher-like IVR message from backend data."""
    name = student.get("name", "Student")
    student_data = student.get("student_data") or {}
    metrics = student.get("metrics") or {}
    insights = student.get("insights") or {}

    improvement = (metrics.get("improvement") or {}).get("examMarksChange")
    subjects = student_data.get("subjectMarks") or {}
    best_subject, weak_subject = _pick_subject_extremes(subjects)
    recommendations = insights.get("recommendations") or []

    parts = [f"Hello {name}."]

    if isinstance(improvement, (int, float)) and improvement > 0:
        parts.append(f"Your marks improved by {int(improvement)} marks.")
    else:
        parts.append("There has not been much improvement yet, but we can improve it.")

    if best_subject and weak_subject and best_subject != weak_subject:
        parts.append(f"You are strong in {best_subject} but need to improve {weak_subject}.")
    elif weak_subject:
        parts.append(f"You should focus a little more on {weak_subject}.")

    if recommendations:
        parts.append(f"I suggest you {recommendations[0]}.")

    parts.append("Keep going, you are improving.")

    return " ".join(parts)


def format_student_data(student: dict) -> str:
    """Backwards-compatible helper used elsewhere in the app."""
    return build_student_feedback(student)
