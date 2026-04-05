import requests
import json
from typing import Dict, Any, List, Optional

from orchestrator.core.docker_client import docker_mgr
from orchestrator.business.inventory_manager import inventory_mgr
from orchestrator.monitor.telemetry import telemetry_collector


def _format_container_list(containers: List[dict], max_lines: Optional[int] = 80) -> str:
    if not containers:
        return "No containers on this host."
    lines = [f"Docker containers ({len(containers)} total):"]
    shown = 0
    for c in sorted(containers, key=lambda x: (x.get("name") or "").lower()):
        if max_lines is not None and len(lines) >= max_lines:
            rest = len(containers) - shown
            if rest > 0:
                lines.append(f"  … {rest} more container(s) not shown.")
            break
        name = c.get("name") or "?"
        status = c.get("status") or "?"
        cid = c.get("id") or "?"
        lines.append(f"  • {name} — {status} ({cid})")
        shown += 1
    return "\n".join(lines)


class ConversationalAgent:
    """The Conversational SysAdmin interface that interprets user prompts
    via the local LLM to execute management tasks.
    """
    max_intents_per_message = 10

    def __init__(self):
        self.active_model = "qwen3.5:latest"
        self.api_url = "http://localhost:11434/api/generate"

        self.system_prompt = '''You are the Conversational SysAdmin for Tloque Nahuaque.
Your job is to read the user's natural language request and map it to intent(s).
You MUST respond with a perfectly valid JSON object and nothing else. Do not include markdown code blocks.

Output format (pick ONE):
1) Single intent — when the user asks for exactly one action:
   {"intent": "<name>", ...optional fields...}
2) Multiple intents — when the user clearly asks for several distinct actions in ONE message (executed in order).
   {"intents": [ {...}, {...} ]}
   Use at most 10 intents. Prefer a single intent when only one task is needed.

Allowed intent names:
- "list_containers": user wants to see Docker containers, status, what is running, docker ps style listing.
- "restart_service": user wants to restart a Docker container. Set "target" to the exact container name (as shown in Docker).
- "stop_service": user wants to stop a running Docker container. Set "target" to the container name.
- "start_service": user wants to start an existing stopped Docker container. Set "target" to the container name.
- "pull_image": user wants to download/pull a Docker image (docker pull). Set "image" to the image reference (e.g. nginx:latest, python:3.12-slim).
- "check_health": user wants overall system / host health (CPU, memory, disk) plus a short Docker summary.
- "consume_inventory": user wants to use or log stock usage. Set "item_id" to the item name/ID and "amount" to the int quantity.
- "unknown": if the request doesn't match any of the above.

Single-intent examples:
{"intent": "list_containers"}
{"intent": "restart_service", "target": "nextcloud"}
{"intent": "stop_service", "target": "redis"}
{"intent": "start_service", "target": "redis"}
{"intent": "pull_image", "image": "nginx:latest"}
{"intent": "check_health"}
{"intent": "consume_inventory", "item_id": "paper_01", "amount": 5}

Multi-intent examples:
{"intents": [{"intent": "list_containers"}, {"intent": "check_health"}]}
{"intents": [{"intent": "pull_image", "image": "alpine:latest"}, {"intent": "list_containers"}]}
'''

    def prompt_ollama(self, user_input: str) -> Dict[str, Any]:
        """Sends the prompt and system instructions to local Ollama"""
        payload = {
            "model": self.active_model,
            "prompt": user_input,
            "system": self.system_prompt,
            "stream": False,
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=100)
            response.raise_for_status()
            data = response.json()
            raw = data.get("response", "{}")
            import re
            raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
            return json.loads(raw)
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

        elif intent == "list_containers":
            if not docker_mgr.client:
                return "Docker is not available. Start Docker Desktop (or the Docker daemon) and try again."
            containers = docker_mgr.list_containers()
            return _format_container_list(containers)

        elif intent == "restart_service":
            target = intent_data.get("target")
            if not target:
                return "Error: Could not identify which container to restart. Say the container name (e.g. the name from `docker ps`)."
            ok, msg = docker_mgr.restart_service(str(target))
            return msg if ok else f"Restart failed: {msg}"

        elif intent == "stop_service":
            target = intent_data.get("target")
            if not target:
                return "Error: Could not identify which container to stop. Provide the container name."
            ok, msg = docker_mgr.stop_container(str(target))
            return msg if ok else f"Stop failed: {msg}"

        elif intent == "start_service":
            target = intent_data.get("target")
            if not target:
                return "Error: Could not identify which container to start. Provide the container name."
            ok, msg = docker_mgr.start_container(str(target))
            return msg if ok else f"Start failed: {msg}"

        elif intent == "pull_image":
            image = intent_data.get("image") or intent_data.get("target")
            if not image:
                return (
                    "Error: Could not identify which image to pull. "
                    "Specify a reference like nginx:latest or quay.io/foo/bar:v1."
                )
            ok, msg = docker_mgr.pull_image(str(image))
            return msg if ok else f"Pull failed: {msg}"

        elif intent == "check_health":
            parts: List[str] = []
            if docker_mgr.client:
                containers = docker_mgr.list_containers()
                running = sum(1 for c in containers if c.get("status") == "running")
                parts.append(
                    f"Docker: {running} running out of {len(containers)} container(s) on this host."
                )
                if len(containers) <= 20:
                    parts.append(_format_container_list(containers, max_lines=25))
                else:
                    parts.append(
                        "(Ask to list containers for the full table; too many to show here.)"
                    )
            else:
                parts.append("Docker: not connected — is Docker Desktop running?")
            try:
                m = telemetry_collector.get_system_metrics()
                parts.append(
                    f"Host: CPU {m['cpu_percent']:.1f}% · RAM {m['memory_percent']:.1f}% used · "
                    f"disk (root) {m['disk_usage']:.1f}% used."
                )
            except Exception as e:
                parts.append(f"Host metrics unavailable: {e}")
            return "\n".join(parts)

        elif intent == "consume_inventory":
            item_id = intent_data.get("item_id")
            amount = intent_data.get("amount", 1)
            try:
                inventory_mgr.consume_item(item_id, amount)
                return f"Successfully logged the consumption of {amount} units of {item_id}. Related supply thresholds have automatically been checked."
            except Exception as e:
                return f"Failed to consume inventory: {str(e)}"

        return "I am sorry, I do not have a defined orchestration protocol for that request."

    def _extract_intent_steps(self, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Turn LLM JSON into an ordered list of single-intent dicts (max max_intents_per_message)."""
        if parsed.get("intent") in ("offline_error", "parse_error"):
            return [parsed]
        raw = parsed.get("intents")
        if isinstance(raw, list) and raw:
            steps = [x for x in raw if isinstance(x, dict) and x.get("intent")]
            if not steps:
                return [{"intent": "unknown"}]
            if len(steps) > self.max_intents_per_message:
                steps = steps[: self.max_intents_per_message]
            return steps
        if isinstance(parsed.get("intent"), str):
            return [parsed]
        return [{"intent": "unknown"}]

    def process_command(self, user_input: str) -> str:
        """Translates natural language into orchestrator engine commands and executes them"""
        print(f"Parsing natural language instruction: '{user_input}'...")
        parsed = self.prompt_ollama(user_input)
        print(f"Parsed JSON Intent: {parsed}")
        steps = self._extract_intent_steps(parsed)
        if len(steps) == 1:
            return self.map_intent_to_action(steps[0])
        blocks: List[str] = []
        total = len(steps)
        for i, step in enumerate(steps, start=1):
            out = self.map_intent_to_action(step)
            blocks.append(f"[Step {i}/{total}]\n{out}")
        return "\n\n---\n\n".join(blocks)

sysadmin_agent = ConversationalAgent()
