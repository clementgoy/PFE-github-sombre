from typing import Any, Dict, List
from ..core.base_agent import BaseAgent


class StructuringAgent(BaseAgent):
    """
    Structuring Agent: Build and Update KG (Steps 7-8).
    Version minimale : normalise une liste d'items et renvoie un résumé.
    """
    SUPPORTED = {"structure_items"}

    def run(self, task: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if task not in self.SUPPORTED:
            return {"error": f"unsupported task '{task}'", "supported": list(self.SUPPORTED)}
        items: List[Dict[str, Any]] = params.get("items") or []
        return {
            "summary": f"{len(items)} éléments structurés.",
            "kg_updates": items,
        }
