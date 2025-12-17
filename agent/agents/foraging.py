from typing import Any, Dict
from ..core.base_agent import BaseAgent


class ForagingAgent(BaseAgent):
    """
    Foraging Agent: Search and Filter (Steps 2-3).
    Lookup simple sur company / investment / investor avec filtres basiques.
    """
    SUPPORTED = {"lookup_company", "lookup_investment", "lookup_investor"}

    def _lookup(self, index: str, es_query: Dict[str, Any], size: int = 10) -> Dict[str, Any]:
        res = self.es_post(f"/{index}/_search", json={"size": size, "query": es_query})
        hits = res.get("hits", {}).get("hits", []) or []
        total = res.get("hits", {}).get("total")
        total_val = total.get("value", 0) if isinstance(total, dict) else 0
        return {
            "summary": f"{total_val} résultats (top {len(hits)}) dans {index}.",
            "items": [h.get("_source", {}) for h in hits],
        }

    def _build_company_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if "label" in params:
            return {"match": {"label": params["label"]}}
        if "label_wildcard" in params:
            return {"wildcard": {"label": {"value": params["label_wildcard"]}}}
        return {"match_all": {}}

    def _build_investor_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if "label" in params:
            return {"match": {"label": params["label"]}}
        if "label_wildcard" in params:
            return {"wildcard": {"label": {"value": params["label_wildcard"]}}}
        return {"match_all": {}}

    def _build_investment_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        q: Dict[str, Any] = {"bool": {"filter": []}}
        if "min_amount" in params:
            q["bool"]["filter"].append({"range": {"raised_amount": {"gte": float(params["min_amount"])}}})
        if "currency_code" in params:
            q["bool"]["filter"].append({"term": {"raised_currency_code": str(params["currency_code"])}})
        if "year_min" in params or "year_max" in params:
            yr: Dict[str, Any] = {}
            if "year_min" in params: yr["gte"] = int(params["year_min"])
            if "year_max" in params: yr["lte"] = int(params["year_max"])
            q["bool"]["filter"].append({"range": {"funded_year": yr}})
        if not q["bool"]["filter"]:
            return {"match_all": {}}
        return q

    def run(self, task: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if task not in self.SUPPORTED:
            return {"error": f"unsupported task '{task}'", "supported": sorted(self.SUPPORTED)}

        size = int(params.get("size", 10))
        params = params or {}

        if task == "lookup_company":
            q = self._build_company_query(params)
            return self._lookup("company", q, size)

        if task == "lookup_investor":
            q = self._build_investor_query(params)
            return self._lookup("investor", q, size)

        if task == "lookup_investment":
            q = self._build_investment_query(params)
            return self._lookup("investment", q, size)

        return {"error": f"unhandled task '{task}'"}
