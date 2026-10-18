# EventPulse — College Event Feedback Analyzer

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
