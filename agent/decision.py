"""REUSABLE DECISION PATTERN: feedback sentiment classifier  (#policy)

What it does
    Classifies college event feedback text as positive, negative, or neutral using Strands
    Decider 2B. The decider reads the tone and intent of the student's natural language and
    returns calibrated probabilities for each sentiment label. When confidence is below the
    threshold, the response is flagged for human review rather than forced into a label.

Typed questions and options
    `sentiment` (choice): positive / negative / neutral; each with a clear one-line definition
    so the decider distinguishes enthusiastic praise from factual reporting and from complaints.

Wiring
    `FeedbackSentimentDecider` is a standalone helper (not an InterventionHandler). The
    `analyze_feedback` tool in tools.py calls it directly:

        clf = FeedbackSentimentDecider(decider)
        result = clf.classify(feedback_text, event_name="Tech Fest 2024")
        result["verdict"]       # "positive" | "negative" | "neutral" | "needs_review"
        result["confidence"]    # float 0..1
        result["decider_ms"]    # int

    The agent collects clf.log (one record per call) and adds it to the decisions list returned
    by HackathonAgent.chat().

How to reuse it
    Copy this file and change the three options in QUESTIONS to match your classification
    categories (e.g. "satisfied / unsatisfied / escalate" for support, or "relevant / irrelevant
    / spam" for content moderation). Adjust CONFIDENCE_THRESHOLD in code to suit your
    acceptable false-positive rate.
"""

from __future__ import annotations

from typing import Any

from decider_kit import Decider

PATTERN_TAG = "#policy"

QUESTIONS = {
    "sentiment": Decider.choice(
        "What is the overall sentiment expressed in this college event feedback?",
        {
            "positive": "the student is satisfied, happy, enthusiastic, or praises the event or its organisation",
            "negative": "the student is dissatisfied, disappointed, frustrated, or criticises the event or its organisation",
            "neutral":  "the student neither praises nor criticises clearly; the response is factual, indifferent, or mixed without a clear lean",
        },
    )
}


def _build_state(feedback_text: str, event_name: str = "") -> str:
    """Build the state string sent to the decider."""
    lines = ["College event feedback to classify:", ""]
    if event_name:
        lines.append(f"Event: {event_name}")
    lines.append(f"Feedback: {feedback_text}")
    return "\n".join(lines)


class FeedbackSentimentDecider:
    """Classifies a single feedback text into positive / negative / neutral."""

    CONFIDENCE_THRESHOLD = 0.6

    def __init__(self, decider: Decider):
        self.decider = decider
        self.log: list[dict[str, Any]] = []

    def classify(self, feedback_text: str, event_name: str = "") -> dict[str, Any]:
        """Classify one feedback text. Returns verdict, label, confidence and decider_ms."""
        state = _build_state(feedback_text, event_name)
        answers = self.decider.ask(state, QUESTIONS)
        a = answers["sentiment"]
        label = a.label or "neutral"
        confidence = round(a.confidence or 0.0, 3)
        if confidence >= self.CONFIDENCE_THRESHOLD:
            verdict = label
        else:
            verdict = "needs_review"
        rec: dict[str, Any] = {
            "pattern": PATTERN_TAG,
            "feedback_text": feedback_text[:120],
            "event_name": event_name,
            "label": label,
            "confidence": confidence,
            "verdict": verdict,
            "decider_ms": round(self.decider.last_latency_ms or 0),
        }
        self.log.append(rec)
        return rec
