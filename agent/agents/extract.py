from typing import Any, Dict
from ..core.base_agent import BaseAgent

class ExtractAgent(BaseAgent):
    """
    Extract Agent: Read and Extract (Step 5).
    Responsible for processing documents/text and extracting specific entities/claims.
    """
    def run(self, task: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Logic to extract info
        return {"status": "Extraction done", "extracted_info": {}}
