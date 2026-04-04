class ConversationalAgent:
    """The Conversational SysAdmin interface that interprets user prompts
    via the local LLM to execute management tasks.
    """
    def __init__(self):
        self.active_model = "llama3"
    
    def process_command(self, user_input: str):
        """Translates natural language into orchestrator engine commands"""
        pass

sysadmin_agent = ConversationalAgent()
