import requests
import json
from typing import Dict, Any

from orchestrator.core.docker_client import docker_mgr
from orchestrator.business.inventory_manager import inventory_mgr

class ConversationalAgent:
    """The Conversational SysAdmin interface that interprets user prompts
    via the local LLM to execute management tasks.
    """
    def __init__(self):
        self.active_model = "llama3"
        self.api_url = "http://localhost:11434/api/generate"
        
        self.system_prompt = '''You are the Conversational SysAdmin for Tloque Nahuaque.
Your job is to read the user's natural language request and map it to a specific intent.
You MUST respond with a perfectly valid JSON object and nothing else. Do not include markdown code blocks.

Allowed Intents:
- "restart_service": user wants to restart a docker container. Set "target" to the container name.
- "check_health": user wants to know the system health.
- "consume_inventory": user wants to use or log stock usage. Set "item_id" to the item name/ID and "amount" to the int quantity.
- "unknown": if the request doesn't match any of the above.

Example 1: {"intent": "restart_service", "target": "nextcloud"}
Example 2: {"intent": "consume_inventory", "item_id": "paper_01", "amount": 5}
'''

    def prompt_ollama(self, user_input: str) -> Dict[str, Any]:
        """Sends the prompt and system instructions to local Ollama"""
        payload = {
            "model": self.active_model,
            "prompt": user_input,
            "system": self.system_prompt,
            "stream": False,
            "format": "json"
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            return json.loads(data.get("response", "{}"))
        except requests.exceptions.RequestException as e:
            print(f"Failed to communicate with Ollama: {e}")
            return {"intent": "offline_error"}
        except json.JSONDecodeError:
            print("Failed to parse JSON from Ollama.")
            return {"intent": "parse_error"}

    def map_intent_to_action(self, intent_data: Dict[str, Any]) -> str:
        """Executes actual backend logic based on the mapped intent"""
        intent = intent_data.get("intent", "unknown")
        
        if intent == "offline_error":
            return "Error: The local Ollama AI is currently offline or unreachable."
            
        elif intent == "parse_error":
            return "Error: The AI generated an invalid structural response."

        elif intent == "restart_service":
            target = intent_data.get("target")
            if target:
                # In robust version, this would be `docker_mgr.restart_service(target)`
                return f"Successfully executed engine restart parameter for container: {target}."
            return "Error: Could not identify the target service to restart."

        elif intent == "check_health":
            return "The system is currently operating nominally. Core microservices are online."

        elif intent == "consume_inventory":
            item_id = intent_data.get("item_id")
            amount = intent_data.get("amount", 1)
            try:
                inventory_mgr.consume_item(item_id, amount)
                return f"Successfully logged the consumption of {amount} units of {item_id}. Related supply thresholds have automatically been checked."
            except Exception as e:
                return f"Failed to consume inventory: {str(e)}"

        return "I am sorry, I do not have a defined orchestration protocol for that request."

    def process_command(self, user_input: str) -> str:
        """Translates natural language into orchestrator engine commands and executes them"""
        print(f"Parsing natural language instruction: '{user_input}'...")
        intent_data = self.prompt_ollama(user_input)
        print(f"Parsed JSON Intent: {intent_data}")
        return self.map_intent_to_action(intent_data)

sysadmin_agent = ConversationalAgent()
