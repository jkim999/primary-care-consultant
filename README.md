An AI-assisted primary care consultation workflow that runs entirely through a colored CLI wrapper around OpenAI’s chat completions API.

Architecture consists of a three-agent pipeline (medical_consultation_system.py): a history-taking agent that gathers required symptom details while scanning for hard-coded red flags, a decision agent that parses the resulting patient JSON to choose self-care vs. escalation with a conservative bias, and a communication agent that rewrites the plan empathetically while preserving safety language. Central configuration in config.py governs model selection, red-flag vocabularies, required questions, escalation timeframes, empathy phrase substitutions, and validation rules, while the enhanced CLI (cli_interface.py) orchestrates user interaction, persists consultation logs, and supports environment- or model-specific runs.

#SETUP
1. Install all dependencies in requirements.txt
2. Set api key using export OPENAI_API_KEY='{key}'
3. Run python cli_interface.py
