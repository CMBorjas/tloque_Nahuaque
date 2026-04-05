import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.ai.nlp_agent import sysadmin_agent

def mock_llm_request():
    test_prompts = [
        "Everything running okay? Check system health.",
        "List all my Docker containers and their status.",
        "Hey, can you quickly restart the nextcloud container for me?",
        "We just used 5 boxes of paper_01, file it."
    ]

    for prompt in test_prompts:
        print(f"\n[USER]: {prompt}")
        # Note: If Ollama isn't actually running locally on port 11434, 
        # this will fall back to "offline error" handling gracefully.
        response = sysadmin_agent.process_command(prompt)
        print(f"[AGENT]: {response}")

if __name__ == "__main__":
    mock_llm_request()
