from typing import Any, Dict, Optional, Callable

class BaseAgent:
    """
    Base class for all agents in the system.
    """
    def __init__(self, es_get: Callable, es_post: Callable):
        self.es_get = es_get
        self.es_post = es_post

    def run(self, task: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task. Should be overridden or utilize a dispatcher like in SpecialistAgent.
        """
        raise NotImplementedError("Agents must implement run()")
