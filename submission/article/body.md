# Same Accuracy, Nearly 7x Faster Decisions: Building EventPulse with Strands Decider 2B

By Yugesh

After every college event -- tech fests, cultural nights, sports days, seminars -- organizers collect hundreds of feedback responses and spend hours reading through them to understand what went well and what did not. EventPulse solves that. It is a conversational agent that classifies each feedback response as positive, negative, or neutral using Strands Decider 2B for the decision and Amazon Bedrock for the conversation. The headline result from a 12-case benchmark: both systems hit 100% accuracy, and the Decider did it at a median of 1,554 ms -- 6.9x faster than an LLM answering the same question.

## The project

EventPulse is for college event organizers and student union committees. They paste in a feedback response (or a batch of them) and get back a sentiment label, a calibrated confidence score, and a flag if the response is too ambiguous to classify automatically.

Features:
- analyze a single feedback response and get a sentiment label (positive, negative, or neutral) with a confidence score from 0 to 1
- batch-analyze a list of responses and get a per-item breakdown plus an aggregate summary
- load sample feedback from 30 synthetic responses across five event types for quick demos
- route responses below the confidence threshold to human review instead of guessing

Here is a real exchange from a demo run:

> **Organizer:** Analyze this feedback from our Tech Fest: "The hackathon was absolutely incredible! I learned so much and the mentors were super helpful."
>
> **EventPulse:** The feedback is **positive** with a confidence score of 0.949. No human review needed. This student had an excellent experience.

> **Organizer:** Now analyze: "The food stalls ran out of food by noon, the queues were huge, and the staff was rude. Terrible experience."
>
> **EventPulse:** This feedback is **negative** with a confidence score of 0.921. These logistical issues are flagged for your team to address.

> **Organizer:** What about this: "The event happened as scheduled. There were workshops in the morning and a competition in the afternoon."
>
> **EventPulse:** This feedback is **neutral** with a confidence score of 0.644. This is near the review threshold -- worth a manual check before drawing conclusions.

Three classifications, three decisions, structured verdicts the organizer can act on directly.

## How I built it

The architecture has three layers. Amazon Bedrock (Amazon Nova Pro) runs the conversation through a Strands Agent. Three tools handle the work: `analyze_feedback` classifies a single response, `batch_analyze` processes a list, and `get_sample_feedback` loads the demo dataset. Strands Decider 2B sits inside `analyze_feedback` -- it receives the feedback text as a state string and returns a calibrated choice over three sentiment labels.

For the data layer, I generated 30 synthetic feedback responses across five college event types (Tech Fest, Cultural Night, Sports Day, Seminar on AI, general events) covering clear positives, clear negatives, factual neutrals, and near-misses like "the keynote was slow but the labs made up for it."

I built the agent using the AWS User Group Madurai hackathon kit and Kiro, starting from a spec in `.kiro/specs/eventpulse/` (requirements, design, tasks) and implementing the four files in `agent/`. The kit's `decider_kit/` library handled the Decider client, the bench runner, and the AgentCore deployment wiring. The agent is deployed on Amazon Bedrock AgentCore Runtime.

< FIGURE 1 of 5: upload submission/article/img/architecture.png here >
Alt text: Architecture: the user, the agent with its tools and decision, Amazon Bedrock and Strands Decider 2B

## The decision I handed to Strands Decider 2B

Sentiment classification is a bounded judgment that benefits from a structured decision model rather than a general-purpose LLM call. An LLM asked "is this positive, negative, or neutral?" works, but it is slow (10+ seconds per call at scale), and returns a word -- not a probability. I need a number to branch on: if confidence is below the threshold, I route the response to human review. An LLM does not give me that directly.

Strands Decider 2B reads the text and returns a probability distribution over the three labels in one forward pass. The question I ask it is:

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

The option descriptions carry most of the signal. "Factual, indifferent, or mixed without a clear lean" is what separates neutral from a weak positive, and the decider reads that distinction from the descriptions, not from the label name alone.

What the agent does with each answer:
- confidence >= 0.7: return the label as the verdict and act on it
- confidence < 0.7: return "needs_review" and tell the organizer to check it manually

On the test split, 7 of 12 cases were answered autonomously at confidence >= 0.7. The other 5 -- mostly neutral and mixed responses -- were flagged for review. That is expected: mixed feedback sits near the boundary between labels, and the decider reflects that uncertainty in its score rather than hiding it.

< FIGURE 1 of 5: upload submission/article/img/architecture.png here >
Alt text: Architecture: the user, the agent with its tools and decision, Amazon Bedrock and Strands Decider 2B

## Measured

The benchmark ran 12 held-out test cases (the "test" split in `agent/eval_cases.jsonl`) through both Strands Decider 2B and an LLM baseline answering the same QUESTIONS. The decider ran on the AWS User Group Madurai hosted API.

Decider: strands-decider-2b-hobson-v19. 12 labelled test cases.

| Metric | Strands Decider 2B | LLM baseline |
|---|---|---|
| Accuracy | 100.0% | 100.0% |
| Median latency | 1,554 ms | 10,791 ms |
| 95th-percentile latency | 1,571 ms | 10,901 ms |
| Autonomous coverage at threshold 0.7 | 58% | 100% |
| Accuracy when answering autonomously | 100.0% | 100.0% |

At the median, the Decider was 6.94x faster. Both systems achieved 100% accuracy on these 12 cases -- this is a small test set and does not establish a general accuracy advantage for either system. The Decider deferred 5 of 12 cases to human review; the LLM answered all 12 autonomously.

Here are three examples from the synthetic dataset the benchmark ran on:

| Feedback | Expected | Verdict | Confidence |
|---|---|---|---|
| "The hackathon was absolutely incredible! I learned so much and the mentors were super helpful." | positive | positive | 0.949 |
| "The food stalls ran out of food by noon. People were waiting in long queues and the staff was rude." | negative | negative | 0.921 |
| "The event happened as scheduled. There were workshops in the morning and a competition in the afternoon." | neutral | neutral | 0.644 |

The neutral case has lower confidence than the clear positives and negatives -- which is expected. A factual sentence with no emotional tone sits near the boundary, and the decider reports that honestly.

< FIGURE 2 of 5: upload submission/article/img/bench-accuracy.png here >
Alt text: Accuracy of Strands Decider 2B and the LLM baseline on the labelled cases

< FIGURE 3 of 5: upload submission/article/img/bench-latency.png here >
Alt text: Median latency per decision for both

< FIGURE 4 of 5: upload submission/article/img/bench-cost.png here >
Alt text: Cost per 1,000 decisions for both

< FIGURE 5 of 5: upload submission/article/img/bench-confidence.png here >
Alt text: Accuracy against the share of decisions answered without a human, as the confidence threshold moves

## The reusable decision pattern

The pattern lives in [`agent/decision.py`](https://github.com/Yugesh-003/eventpulse/blob/main/agent/decision.py), labelled `REUSABLE DECISION PATTERN: feedback sentiment classifier (#policy)`.

To drop it into your own agent:
1. Copy `agent/decision.py` into your project.
2. Change the three options in `QUESTIONS` to your own categories -- for example, "satisfied / unsatisfied / escalate" for a support agent, or "relevant / irrelevant / spam" for content moderation.
3. Instantiate `FeedbackSentimentDecider(Decider())` in your tool and call `clf.classify(text)`.
4. Branch on `result["verdict"]` and `result["confidence"]` in your code.
5. Adjust `CONFIDENCE_THRESHOLD` to match your tolerance for false positives versus flagged cases.

The wiring is a standalone helper, not an `InterventionHandler`, so it works in any tool or pre-agent step without requiring a Strands intervention seam.

## What I learned and what is next

The biggest thing I learned is that the option descriptions matter more than the question text. My first version had terse descriptions like "positive response" and the decider struggled with mixed feedback. Adding "the student neither praises nor criticises clearly; the response is factual, indifferent, or mixed without a clear lean" to the neutral option fixed most of the ambiguous cases immediately.

The 58% autonomous coverage on the test split is lower than I would want for a production tool. Next steps: run the benchmark on a larger set of real feedback from actual college events, tune the confidence threshold per sentiment class (neutral likely needs a lower threshold than positive or negative), and add a second question asking which aspect of the event the feedback covers (venue, food, speaker, organization) to give organizers more actionable breakdowns.

---

Code: https://github.com/Yugesh-003/eventpulse . Video: (add YouTube/Vimeo link after recording) . Tags: #strands-decider-2b #policy

Built with the AWS User Group Madurai Strands Decider hackathon kit
