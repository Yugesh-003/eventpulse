"""EventPulse: college event feedback sentiment analyzer.

    from agent.agent import HackathonAgent
    out = HackathonAgent().chat("Analyze this feedback: The hackathon was amazing!")
    out["reply"], out["decisions"]
"""

from __future__ import annotations

import time
from typing import Any

from strands import Agent

from decider_kit import Decider
from decider_kit.llm import agent_model, default_model_id, strip_thinking

from .decision import FeedbackSentimentDecider
from .tools import TOOLS, _classifier

NAME = "EventPulse — College Event Feedback Analyzer"

SYSTEM_PROMPT = """You are EventPulse, a college event feedback analyzer. You help event organizers
and student union committees understand how students felt about their events.

You can:
- Analyze a single feedback response and classify its sentiment as positive, negative, or neutral
- Batch-analyze a list of feedback responses and give a summary breakdown
- Load sample feedback to demonstrate your capabilities

When analyzing feedback, always mention:
1. The sentiment verdict (positive / negative / neutral)
2. The confidence score (0 to 1)
3. Whether the item needs human review (when confidence is below 0.6)

Be concise, helpful, and professional. When confidence is low, suggest the organizer review
the response manually before drawing conclusions."""


class HackathonAgent:
    """EventPulse agent: one Strands agent per session, with the sentiment decision wired in."""

    def __init__(self, decider: Decider | None = None, model_id: str | None = None, eager: bool | None = None):
        self.decider = decider or Decider()
        self.model_id = model_id or default_model_id()
        # eager is accepted for API compatibility but EventPulse doesn't use an eager mode
        self.sessions: dict[str, tuple[Agent, FeedbackSentimentDecider]] = {}

    def _session(self, session_id: str) -> tuple[Agent, FeedbackSentimentDecider]:
        if session_id not in self.sessions:
            # Each session gets its own classifier so logs are per-session
            clf = FeedbackSentimentDecider(self.decider)
            # Patch the module-level classifier used by tools so this session's log is captured
            import agent.tools as tools_mod
            tools_mod._classifier = clf
            agent = Agent(
                model=agent_model(self.model_id),
                system_prompt=SYSTEM_PROMPT,
                tools=TOOLS,
                callback_handler=None,
            )
            self.sessions[session_id] = (agent, clf)
        return self.sessions[session_id]

    def chat(self, message: str, session_id: str = "default", images: list[Any] | None = None) -> dict[str, Any]:
        """Send a message to EventPulse and get a reply with decision metadata."""
        agent, clf = self._session(session_id)
        before = len(clf.log)
        t0 = time.perf_counter()
        result = agent(message)
        reply = strip_thinking(str(result))
        return {
            "reply": reply,
            "decisions": clf.log[before:],
            "model_id": self.model_id,
            "latency_ms": round((time.perf_counter() - t0) * 1000),
            "agent": NAME,
            "eager": False,
        }


if __name__ == "__main__":
    import json
    import sys

    a = HackathonAgent()
    msgs = sys.argv[1:] or [
        "Analyze this feedback: The hackathon was incredible, best event of the year!",
        "Now analyze: The venue was too hot and the food ran out early. Very disappointing.",
        "Can you show me some sample feedback?",
    ]
    for msg in msgs:
        print(json.dumps(a.chat(msg), indent=2))
