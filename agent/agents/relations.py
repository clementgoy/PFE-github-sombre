from typing import Any, Dict, List
from ..core.base_agent import BaseAgent


class RelationsAgent(BaseAgent):
    """
    Relations Agent: Search Relations (Step 6).
    Implémente un join générique via Siren Federate + fallback simple.
    """
    SUPPORTED = {"join"}

    def _fallback(self, parent_index: str, es_query: Dict[str, Any], size: int) -> Dict[str, Any]:
        # Lookup direct sans join, utile pour donner un minimum de signal.
        res = self.es_post(f"/{parent_index}/_search", json={"size": size, "query": es_query})
        hits = res.get("hits", {}).get("hits", []) or []
        total = res.get("hits", {}).get("total")
        total_val = total.get("value", 0) if isinstance(total, dict) else 0
        return {
            "summary": f"Fallback lookup: {total_val} résultats (top {len(hits)}) dans {parent_index}.",
            "items": [h.get("_source", {}) for h in hits],
        }

    def run(self, task: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if task not in self.SUPPORTED:
            return {"error": f"unsupported task '{task}'", "supported": sorted(self.SUPPORTED)}

        parent_index = params.get("parent_index")
        child_index = params.get("child_index")
        on: List[str] = params.get("on") or []
        es_query = params.get("es_query") or {"match_all": {}}
        size = int(params.get("size", 10))

        if not (parent_index and child_index and len(on) == 2):
            return {"error": "join needs parent_index, child_index, on=[child_key,parent_key]"}

        join = {"indices": [child_index], "on": on}
        if es_query:
            join["request"] = {"query": es_query}

        try:
            res = self.es_post(f"/siren/{parent_index}/_search",
                               json={"size": size, "query": {"join": join}})
        except Exception as e:
            return {"error": f"join failed: {e}"}

        hits = res.get("hits", {}).get("hits", []) or []
        total = res.get("hits", {}).get("total")
        total_val = total.get("value", 0) if isinstance(total, dict) else 0

        if total_val > 0:
            return {
                "summary": f"{total_val} résultats (top {len(hits)}) via join {parent_index}<-{child_index} on {on}.",
                "items": [h.get("_source", {}) for h in hits],
            }

        # Fallback si join vide
        fb = self._fallback(parent_index, es_query, size)
        fb["note"] = "join returned 0 results"
        return fb
