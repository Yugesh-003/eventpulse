# EventPulse — College Event Feedback Analyzer

**Instantly understand how students felt about your college event — powered by Strands Decider 2B.**

An agent on AWS that hands one decision to **Strands Decider 2B** and the conversation to **Amazon Bedrock**. Decision pattern: `#policy`. Tags: `#strands-decider-2b` `#policy`.

- Video: (add the YouTube/Vimeo link)
- Article: (add the AWS Builder Center link)
- Deployed: run `./kit deploy`

## The project

- **Pitch:** Instantly understand how students felt about your college event — powered by Strands Decider 2B.
- **Who it is for:** Event organizers and student union committees who collect feedback after college events (tech fests, cultural nights, sports days, seminars) and want a fast, calibrated read on student sentiment.
- **Features:**
  - analyze a single feedback response and get a sentiment label (positive / negative / neutral) with confidence;
  - batch-analyze a list of responses and get a full breakdown summary;
  - load sample feedback for quick demos and testing;
  - low-confidence responses (below 0.6) are flagged as "needs review" instead of being forced into a label;
  - deployed on Amazon Bedrock AgentCore Runtime.
- **The decision handed to Strands Decider 2B:** for each feedback text, what is the overall sentiment — positive, negative, or neutral? (`#policy`)
- **Why a decision model:** sentiment classification runs on every response and must be fast, cheap, and return calibrated probabilities the code can branch on. The decider reads the tone and intent of natural language without needing a fine-tuned classifier.
- **Amazon Bedrock:** the conversation and tool use (Amazon Nova Pro by default).



## How it is built

Strands Agents with Amazon Bedrock for the generative part, the tools in `agent/tools.py`, deployed to Amazon Bedrock AgentCore Runtime, and one decision handed to Strands Decider 2B at a clear seam in the agent's path.

Every Amazon Bedrock model id is set in `.env` (`BEDROCK_MODEL_ID`, and `BEDROCK_SMALL/MEDIUM/LARGE_MODEL_ID` for routing), Amazon Nova by default.



## Reusable decision pattern: feedback sentiment classifier  (#policy)

The pattern lives in [`agent/decision.py`](agent/decision.py), labelled `REUSABLE DECISION PATTERN`. It contains the typed questions and their options, the wiring that puts the decision in the agent's path, and a note on how to reuse it:

```text
REUSABLE DECISION PATTERN: feedback sentiment classifier  (#policy)

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
```

Typed questions:

```python
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
```

## Measured

Decider: strands-decider-2b-hobson-v19 (ugmdu). 12 labelled cases, 12 decisions.

| | Strands Decider 2B | qwen3.5-4b |
|---|---|---|
| Accuracy | 100.0% | 100.0% |
| Latency p50 per decision | 1554 ms | 10790 ms |
| Latency p95 | 1571 ms | 10901 ms |
| Cost per 1,000 decisions | $0.0350 | $0.0000 |
| Answered alone at confidence >= 0.7 | 58% | 100% |
| Accuracy when confident | 100.0% | 100.0% |

At the median the decider was 6.9x faster than the LLM.

Reproduce with `./kit bench` (cases in `agent/eval_cases.jsonl`; charts in `submission/bench/`).

## Run it

```bash
./kit setup        # checks your machine and AWS, sets up Strands Decider 2B (local model or hosted API)
./kit demo         # web UI at http://localhost:8501
./kit bench        # the decision vs an Amazon Bedrock LLM
./kit deploy       # Amazon Bedrock AgentCore Runtime
```

Requirements: Python 3.10+, AWS credentials with Amazon Bedrock access, and for deploying, Node 20+ with the AgentCore CLI (`./kit agentcore-cli`).

## Credits

Built with the AWS User Group Madurai Strands Decider hackathon kit (https://github.com/awsugmdu). The kit's reusable library (`decider_kit/`, the demo UI, the video and article tooling, and the Kiro steering, skills and hooks) is the user group's; the agent in `agent/` is mine. Strands Decider: https://github.com/strands-labs/strands-decider (Apache-2.0).

Licence: Apache-2.0 (see LICENSE).
