from typing import Any, Dict, List
from .base_agent import BaseAgent


class Coordinator(BaseAgent):
    """
    LLM Coordinator - Plan HTN and Scheduling.
    Routage basique vers les agents enregistrés selon leurs tâches supportées.
    """

    def __init__(self, es_get_func, es_post_func, llm_client=None):
        super().__init__(es_get_func, es_post_func)
        self.llm_client = llm_client
        self.agents: Dict[str, BaseAgent] = {}

    def register_agent(self, name: str, agent: BaseAgent):
        self.agents[name] = agent

    def _agent_supports(self, agent: BaseAgent, task: str) -> bool:
        # Specialist expose SUPPORTED_TASKS, Foraging/Relations/Structuring exposent SUPPORTED
        if hasattr(agent, "SUPPORTED_TASKS") and task in getattr(agent, "SUPPORTED_TASKS", []):
            return True
        if hasattr(agent, "SUPPORTED") and task in getattr(agent, "SUPPORTED", []):
            return True
        return False

    def run(self, task: str, params: Dict[str, Any]) -> Dict[str, Any]:
        for name, agent in self.agents.items():
            if self._agent_supports(agent, task):
                return agent.run(task, params)
        return {"error": f"no agent registered for task '{task}'",
                "known_agents": list(self.agents.keys())}
