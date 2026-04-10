"""
ai_agent.py — LangGraph-based AI Agent for Student Insights
=============================================================
Uses LangGraph to orchestrate a simple reasoning pipeline:
  1. Analyze student performance data
  2. Identify strengths and weaknesses
  3. Generate a friendly, concise voice-ready summary

The agent uses Mistral (via LangChain's ChatMistralAI) by default.
Set MISTRAL_API_KEY in your environment, or it falls back to a
rule-based template response.
"""

import os
import logging
from typing import TypedDict, Annotated

logger = logging.getLogger("campus++.services.ai_agent")

# ── Try importing LangGraph + LangChain ───────────────────────
try:
    from langgraph.graph import StateGraph, END
    from langchain_mistralai import ChatMistralAI
    from langchain_core.messages import HumanMessage, SystemMessage

    LANGGRAPH_AVAILABLE = True
    logger.info("✅ LangGraph + LangChain Mistral loaded successfully")
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning(
        "⚠️  LangGraph or LangChain Mistral not installed. "
        "Falling back to rule-based response generator."
    )


# ── State Definition ──────────────────────────────────────────
class AgentState(TypedDict):
    student_data: str           # raw student performance text
    analysis: str               # intermediate analysis
    response: str               # final voice-ready response


# ── System Prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are Campus++, a friendly AI academic assistant that speaks to students over phone calls.

Your job is to analyze a student's academic performance data and give a SHORT, friendly, conversational summary.

Rules:
1. Keep it to 4-5 sentences MAX (this is for a phone call, not a report).
2. Use a warm, Hinglish-friendly tone — be encouraging, not robotic.
3. Mention specific numbers (attendance %, marks, quiz scores).
4. Highlight ONE strength and ONE area to improve.
5. End with a motivational line.
6. Do NOT use bullet points, markdown, or special characters — plain spoken text only.
7. Do NOT start with "Hello" or greetings — the system already greeted them.

Example style:
"Dekho, your attendance is 75 percent which is okay but can definitely improve. Your marks at 68 percent show you understand the concepts. Computer Science is your strongest subject at 80 percent, great job! But English at 55 percent needs some attention, try reading more. Overall you're on the right track, keep pushing and you'll do amazing!"
"""


# ═══════════════════════════════════════════════════════════════
#  LangGraph Agent (used when dependencies are available)
# ═══════════════════════════════════════════════════════════════

def _build_langgraph_agent():
    """Build and compile the LangGraph state machine."""

    model = ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY", ""),
        temperature=0.7,
        max_tokens=300,
    )

    # ── Node: Analyze Performance ─────────────────────────────
    def analyze_performance(state: AgentState) -> dict:
        """First node — parse and understand the student data."""
        logger.info("🔍 Analyzing student performance data...")
        student_data = state["student_data"]

        messages = [
            SystemMessage(content=(
                "You are an academic data analyst. "
                "From the following student data, identify:\n"
                "1. Overall performance level (Excellent/Good/Average/Poor)\n"
                "2. Strongest area\n"
                "3. Weakest area\n"
                "4. Key risk factors\n"
                "Keep the analysis brief — 3-4 lines max."
            )),
            HumanMessage(content=student_data),
        ]

        result = model.invoke(messages)
        logger.info(f"📊 Analysis complete: {result.content[:80]}...")
        return {"analysis": result.content}

    # ── Node: Generate Voice Response ─────────────────────────
    def generate_response(state: AgentState) -> dict:
        """Second node — produce voice-ready summary."""
        logger.info("🎙️ Generating voice-ready response...")

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=(
                f"Student Data:\n{state['student_data']}\n\n"
                f"Analysis:\n{state['analysis']}\n\n"
                "Now generate the spoken response for the phone call."
            )),
        ]

        result = model.invoke(messages)
        response_text = result.content.strip()
        logger.info(f"🗣️ Voice response ready: {response_text[:80]}...")
        return {"response": response_text}

    # ── Build Graph ───────────────────────────────────────────
    graph = StateGraph(AgentState)
    graph.add_node("analyze", analyze_performance)
    graph.add_node("respond", generate_response)

    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "respond")
    graph.add_edge("respond", END)

    return graph.compile()


# ═══════════════════════════════════════════════════════════════
#  Rule-Based Fallback (no external API needed)
# ═══════════════════════════════════════════════════════════════

def _rule_based_response(student_data: str) -> str:
    """
    Generate a response using simple rules when LLM is unavailable.
    Parses the student_data text to extract numbers and build a response.
    """
    logger.info("🔧 Using rule-based fallback response generator")

    # Parse key metrics from the formatted text
    lines = student_data.strip().split("\n")
    data = {}
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()

    name = data.get("Student Name", "Student")
    attendance = data.get("Attendance", "N/A")
    marks = data.get("Overall Marks", "N/A")
    quiz_avg = data.get("Quiz Average", "N/A")
    risk_level = data.get("Risk Level", "Unknown")

    # Parse subject-wise to find best and worst
    subjects_str = data.get("Subject-wise Marks", "")
    best_subject = "your studies"
    worst_subject = "some subjects"
    if subjects_str:
        subjects = {}
        for part in subjects_str.split(","):
            part = part.strip()
            if ":" in part:
                sub_name, sub_score = part.rsplit(":", 1)
                try:
                    subjects[sub_name.strip()] = int(
                        sub_score.strip().replace("%", "")
                    )
                except ValueError:
                    pass
        if subjects:
            best_subject = max(subjects, key=subjects.get)
            worst_subject = min(subjects, key=subjects.get)

    # Build response based on risk level
    att_val = attendance.replace("%", "")
    try:
        att_num = int(att_val)
    except ValueError:
        att_num = 0

    if risk_level == "High":
        tone = (
            f"Dekho {name}, attendance {attendance} hai, jo abhi low side par hai "
            f"and isko urgent improve karna zaroori hai. "
            f"Tumhare marks {marks} hain aur quiz average {quiz_avg} hai. "
            f"{best_subject} tumhara strong area lag raha hai, ye positive point hai. "
            f"Lekin {worst_subject} par extra focus chahiye. "
            f"Tension mat lo, daily study plan banao and faculty se help lo, "
            f"step by step performance improve hoga."
        )
    elif risk_level == "Medium":
        tone = (
            f"{name}, quick update suno. Attendance {attendance} hai, decent hai "
            f"but aur better ho sakti hai. "
            f"Marks {marks} aur quiz average {quiz_avg} dikhata hai ki basics clear hain. "
            f"{best_subject} tumhara strong point hai, great going. "
            f"Bas {worst_subject} par thoda extra practice karo and overall score "
            f"jaldi improve hoga. Tum sahi track par ho, keep going."
        )
    else:  # Low risk = good performance
        tone = (
            f"Bahut badhiya {name}, tumhari performance strong chal rahi hai. "
            f"Attendance {attendance} excellent range me hai. "
            f"Marks {marks} aur quiz average {quiz_avg} kaafi impressive hai. "
            f"{best_subject} tumhara star subject hai, isi consistency ko maintain karo. "
            f"Saath me {worst_subject} par halka sa focus rakho for balance. "
            f"Overall superb progress, aise hi continue karo."
        )

    return tone


# ═══════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════

async def generate_student_insights(student_data: str) -> str:
    """
    Main entry point — generates a voice-ready performance summary.

    Uses LangGraph + Mistral when available, otherwise falls
    back to rule-based generation.

    Args:
        student_data: Formatted student performance text.

    Returns:
        A concise, spoken-word-friendly summary string.
    """
    logger.info("🧠 Generating student insights...")

    # ── Try LangGraph agent first ─────────────────────────────
    if LANGGRAPH_AVAILABLE and os.getenv("MISTRAL_API_KEY"):
        try:
            agent = _build_langgraph_agent()
            result = agent.invoke({
                "student_data": student_data,
                "analysis": "",
                "response": "",
            })
            response = result.get("response", "")
            if response:
                logger.info("✅ LangGraph agent response generated")
                return response
        except Exception as e:
            logger.error(f"💥 LangGraph agent failed: {e}")
            logger.info("⬇️  Falling back to rule-based response")

    # ── Fallback to rule-based ────────────────────────────────
    return _rule_based_response(student_data)
