# EventPulse Design

## State text layout

The decider receives the raw feedback text, prefixed with event context when available:

```
College event feedback to classify:

Event: <event_name>
Feedback: <feedback_text>
```

When no event name is available:

```
College event feedback to classify:

Feedback: <feedback_text>
```

## Typed questions and options

```python
QUESTIONS = {
    "sentiment": Decider.choice(
        "What is the overall sentiment expressed in this college event feedback?",
        {
            "positive": "the student is satisfied, happy, enthusiastic or praises the event",
            "negative": "the student is dissatisfied, disappointed, frustrated or criticises the event",
            "neutral":  "the student neither praises nor criticises; factual, indifferent or mixed without clear lean",
        }
    )
}
```

## Thresholds and actions

| Condition | Verdict |
|---|---|
| `confidence >= 0.6` | label = predicted sentiment |
| `confidence < 0.6` | verdict = `needs_review` |

The threshold 0.6 is set in `FeedbackSentimentDecider.CONFIDENCE_THRESHOLD`.

## Seam

This is a **direct call** pattern: the wiring is not an `InterventionHandler`. The agent calls the
decider inside the `analyze_feedback` tool, which is invoked by the Strands Agent per request.
The tool returns the verdict and confidence; the agent formats the reply.

```
User message
  → Strands Agent (Bedrock LLM)
    → analyze_feedback tool
      → FeedbackSentimentDecider.classify(text, event_name)
        → Decider.ask(state, QUESTIONS)
        → applies threshold → verdict
      ← returns {label, confidence, verdict, decider_ms}
    ← tool result
  ← agent reply
```

## Tools

| Tool | Purpose |
|---|---|
| `analyze_feedback(feedback_text, event_name)` | classify one feedback item |
| `batch_analyze(feedback_list, event_name)` | classify a JSON list and return summary |
| `get_sample_feedback()` | load examples from `agent/data/feedback.json` |

## Eval-case plan

24 cases across every branch:

| Branch | Count | Split |
|---|---|---|
| Clear positive feedback | 6 | 3 tune / 3 test |
| Clear negative feedback | 6 | 3 tune / 3 test |
| Clear neutral / mixed | 4 | 2 tune / 2 test |
| Near-miss: mildly positive could read neutral | 3 | 1 tune / 2 test |
| Near-miss: complaint with one positive note | 3 | 2 tune / 1 test |
| Low confidence / ambiguous | 2 | 1 tune / 1 test |

Total: 24 cases, 12 tune / 12 test.
