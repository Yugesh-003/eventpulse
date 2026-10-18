# EventPulse Tasks

- [x] Write requirements.md
- [x] Write design.md
- [x] Write AGENT.md
- [x] Generate synthetic feedback data (agent/data/feedback.json)
- [x] Implement agent/decision.py (FeedbackSentimentDecider, PATTERN_TAG, QUESTIONS)
- [x] Implement agent/tools.py (analyze_feedback, batch_analyze, get_sample_feedback)
- [x] Implement agent/agent.py (HackathonAgent, NAME, SYSTEM_PROMPT)
- [x] Write agent/eval_cases.jsonl (24 cases, 12 tune / 12 test)
- [x] Write agent/demo_script.yaml
- [x] Update agent/features.yaml (Runtime only)
- [ ] Run ./kit test (fix until green)
- [ ] Run ./kit run (fix until green)
- [ ] Run ./kit bench --split tune (tune if needed)
- [ ] Run ./kit bench --split test (report numbers)
