"""
student_service.py - Student Data Layer
=======================================
Provides mock student data and lookup utilities.
Replace MOCK_STUDENTS with MongoDB queries for production.
"""

import logging
from typing import Optional

logger = logging.getLogger("campus++.services.student")

MOCK_STUDENTS: dict[str, dict] = {
    "1234": {
        "studentId": "1234",
        "name": "Rahul Sharma",
        "verificationPin": "1234",
        "attendance": 75,
        "marks": 68,
        "quizAvg": 60,
        "riskLevel": "Medium",
        "subjects": {
            "Mathematics": 72,
            "Physics": 65,
            "Computer Science": 80,
            "English": 55,
        },
    },
    "5678": {
        "studentId": "5678",
        "name": "Priya Patel",
        "verificationPin": "5678",
        "attendance": 92,
        "marks": 88,
        "quizAvg": 85,
        "riskLevel": "Low",
        "subjects": {
            "Mathematics": 90,
            "Physics": 85,
            "Computer Science": 92,
            "English": 84,
        },
    },
    "9999": {
        "studentId": "9999",
        "name": "Amit Kumar",
        "verificationPin": "9999",
        "attendance": 50,
        "marks": 42,
        "quizAvg": 35,
        "riskLevel": "High",
        "subjects": {
            "Mathematics": 38,
            "Physics": 45,
            "Computer Science": 48,
            "English": 37,
        },
    },
}


def get_student(student_id: str) -> Optional[dict]:
    """Look up a student by student ID."""
    student = MOCK_STUDENTS.get(student_id)
    if student:
        logger.info(f"Found student: {student['name']} (ID: {student_id})")
    else:
        logger.warning(f"Student not found for ID: {student_id}")
    return student


def verify_student_pin(student: dict, entered_pin: str) -> bool:
    """Verify keypad PIN against stored PIN."""
    expected_pin = str(student.get("verificationPin", "")).strip()
    return bool(expected_pin) and entered_pin.strip() == expected_pin


def format_student_data(student: dict) -> str:
    """Format student data for AI agent context."""
    subjects_str = ", ".join(
        f"{subject}: {score}%" for subject, score in student.get("subjects", {}).items()
    )

    return (
        f"Student Name: {student['name']}\n"
        f"Student ID: {student['studentId']}\n"
        f"Attendance: {student['attendance']}%\n"
        f"Overall Marks: {student['marks']}%\n"
        f"Quiz Average: {student['quizAvg']}%\n"
        f"Risk Level: {student['riskLevel']}\n"
        f"Subject-wise Marks: {subjects_str}\n"
    )
