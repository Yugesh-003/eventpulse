"""EventPulse tools: analyze college event feedback sentiment using Strands Decider 2B."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from strands import tool

from decider_kit import Decider

from .decision import FeedbackSentimentDecider

# Module-level classifier shared across tool calls within a session
_decider = Decider()
_classifier = FeedbackSentimentDecider(_decider)

_DATA_FILE = Path(__file__).parent / "data" / "feedback.json"


def _load_feedback() -> list[dict[str, Any]]:
    """Load feedback samples from the local data file."""
    if _DATA_FILE.exists():
        return json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    return []


@tool
def analyze_feedback(feedback_text: str, event_name: str = "") -> dict[str, Any]:
    """Analyze a single feedback response and return its sentiment label and confidence score."""
    if not feedback_text or not feedback_text.strip():
        return {"error": "feedback_text is required and cannot be empty"}
    result = _classifier.classify(feedback_text.strip(), event_name.strip())
    return {
        "verdict": result["verdict"],
        "label": result["label"],
        "confidence": result["confidence"],
        "decider_ms": result["decider_ms"],
        "needs_review": result["verdict"] == "needs_review",
    }


@tool
def batch_analyze(feedback_list: str, event_name: str = "") -> dict[str, Any]:
    """Analyze a JSON list of feedback strings and return per-item results and a summary breakdown."""
    try:
        items: list[str] = json.loads(feedback_list)
        if not isinstance(items, list):
            return {"error": "feedback_list must be a JSON array of strings"}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}

    results = []
    counts: dict[str, int] = {"positive": 0, "negative": 0, "neutral": 0, "needs_review": 0}
    flagged = []

    for i, text in enumerate(items):
        if not isinstance(text, str) or not text.strip():
            results.append({"index": i, "error": "empty or invalid item"})
            continue
        r = _classifier.classify(text.strip(), event_name.strip())
        entry = {
            "index": i,
            "feedback": text[:80] + ("..." if len(text) > 80 else ""),
            "verdict": r["verdict"],
            "confidence": r["confidence"],
        }
        results.append(entry)
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        if r["verdict"] == "needs_review":
            flagged.append(i)

    total = len(items)
    return {
        "total": total,
        "summary": counts,
        "flagged_for_review": flagged,
        "results": results,
    }


@tool
def get_sample_feedback(n: int = 5) -> dict[str, Any]:
    """Load sample college event feedback responses for demonstration and testing."""
    samples = _load_feedback()
    if not samples:
        return {"error": "No sample data found. Run ./kit data to generate it."}
    selected = samples[: max(1, min(n, len(samples)))]
    return {
        "count": len(selected),
        "samples": [{"id": s["id"], "event": s["event"], "feedback": s["feedback"]} for s in selected],
    }


TOOLS = [analyze_feedback, batch_analyze, get_sample_feedback]
