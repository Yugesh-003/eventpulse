# EventPulse Requirements

## Users
Event organizers and student union committees at colleges who want to quickly understand student sentiment from post-event feedback.

## User Stories

1. **Single feedback analysis**
   - WHEN an organizer submits a feedback text, THE agent SHALL ask Strands Decider 2B "what is the sentiment of this feedback?" BEFORE returning a label, so the classification is calibrated and confidence-aware.
   - The agent SHALL return the sentiment label (positive / negative / neutral), the confidence score, and a brief explanation.
   - WHEN the decider confidence is below 0.6, THE agent SHALL flag the response as "needs review" instead of forcing a label.

2. **Batch analysis**
   - WHEN an organizer requests a batch analysis, THE agent SHALL analyze each feedback item individually and return a summary breakdown (counts per sentiment, list of flagged items).

3. **Sample feedback**
   - WHEN an organizer asks for examples, THE agent SHALL load sample college event feedback from the local dataset.

4. **Paired with Amazon Bedrock**
   - The conversation, tool orchestration and any text generation SHALL use Amazon Bedrock (Amazon Nova Pro by default) via the Strands Agents SDK.
   - Strands Decider 2B SHALL handle the sentiment classification decision.

## Acceptance Criteria (EARS)

- WHEN a positive feedback text is submitted, THE system SHALL return label "positive" with confidence ≥ 0.6 at least 80% of the time on the test split.
- WHEN a negative feedback text is submitted, THE system SHALL return label "negative" with confidence ≥ 0.6 at least 80% of the time on the test split.
- WHEN the decider confidence is < 0.6, THE system SHALL return verdict "needs_review" and NOT assign a definitive label.
- WHEN multiple feedback items are submitted, THE system SHALL return per-item results and an aggregate summary.
- THE agent SHALL NOT call boto3 or any provider SDK directly; all LLM calls SHALL go through `decider_kit.llm.agent_model`.
