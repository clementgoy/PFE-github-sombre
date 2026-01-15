from typing import Any, Dict, List, Set
from ..core.base_agent import BaseAgent


class RelationsAgent(BaseAgent):
    """
    Relations Agent: Search Relations (Step 6).
    - join générique via Siren Federate + fallback lookup
    - find_paths_between_entities (profondeur 2) sur company / investor.
    """
    SUPPORTED = {"join", "find_paths_between_entities"}

    # --- helpers de lookup ---
    def _lookup_company_id(self, label: str) -> str | None:
        q = {"term": {"label.raw": label}}
        res = self.es_post("/company/_search", json={"size": 1, "query": q})
        hits = res.get("hits", {}).get("hits", [])
        if not hits:
            q = {"term": {"label": label}}
            res = self.es_post("/company/_search", json={"size": 1, "query": q})
            hits = res.get("hits", {}).get("hits", [])
            if not hits:
                return None
        return hits[0].get("_source", {}).get("id")

    def _lookup_investor_id(self, label: str) -> str | None:
        q = {"term": {"label.raw": label}}
        res = self.es_post("/investor/_search", json={"size": 1, "query": q})
        hits = res.get("hits", {}).get("hits", [])
        if not hits:
            q = {"term": {"label": label}}
            res = self.es_post("/investor/_search", json={"size": 1, "query": q})
            hits = res.get("hits", {}).get("hits", [])
            if not hits:
                return None
        return hits[0].get("_source", {}).get("id")

    def _fallback(self, parent_index: str, es_query: Dict[str, Any], size: int) -> Dict[str, Any]:
        res = self.es_post(f"/{parent_index}/_search", json={"size": size, "query": es_query})
        hits = res.get("hits", {}).get("hits", []) or []
        total = res.get("hits", {}).get("total")
        total_val = total.get("value", 0) if isinstance(total, dict) else 0
        return {
            "summary": f"Fallback lookup: {total_val} résultats (top {len(hits)}) dans {parent_index}.",
            "items": [h.get("_source", {}) for h in hits],
        }

    # --- path finder helpers ---
    def _filter_investments(self, base_query: Dict[str, Any], year_min: int | None, year_max: int | None,
                            currency: str | None, size: int = 200):
        q = {"bool": {"filter": []}}
        if base_query:
            q["bool"]["filter"].append(base_query)
        if year_min is not None or year_max is not None:
            yr = {}
            if year_min is not None:
                yr["gte"] = int(year_min)
            if year_max is not None:
                yr["lte"] = int(year_max)
            q["bool"]["filter"].append({"range": {"funded_year": yr}})
        if currency:
            q["bool"]["filter"].append({"term": {"raised_currency_code": currency}})
        if not q["bool"]["filter"]:
            q = {"match_all": {}}
        return self.es_post("/investment/_search", json={"size": size, "query": q})

    def _resolve_id(self, label_or_id: str, ent_type: str) -> str | None:
        if label_or_id.startswith("company/") or label_or_id.startswith("financial-organization/") or label_or_id.startswith("person/"):
            return label_or_id
        if ent_type == "company":
            return self._lookup_company_id(label_or_id)
        if ent_type == "investor":
            return self._lookup_investor_id(label_or_id)
        return None

    # --- BFS bipartite (company <-> investor) jusqu'à profondeur 4 ---
    def _build_bipartite(self, year_min, year_max, currency, size: int = 500):
        res = self._filter_investments(None, year_min, year_max, currency, size=size)
        comp_to_inv: Dict[str, Set[str]] = {}
        inv_to_comp: Dict[str, Set[str]] = {}
        for h in res.get("hits", {}).get("hits", []) or []:
            s = h.get("_source", {}) or {}
            comps = s.get("companies", []) or []
            invs = s.get("investors", []) or []
            for c in comps:
                comp_to_inv.setdefault(c, set()).update(invs)
            for iv in invs:
                inv_to_comp.setdefault(iv, set()).update(comps)
        return comp_to_inv, inv_to_comp

    def _bfs_paths_depth4(self, id_a: str, type_a: str, id_b: str, type_b: str,
                          year_min, year_max, currency, max_paths: int):
        comp_to_inv, inv_to_comp = self._build_bipartite(year_min, year_max, currency, size=max_paths * 50)

        def neighbors(node_id: str, ntype: str) -> List[tuple[str, str]]:
            if ntype == "company":
                return [(iv, "investor") for iv in comp_to_inv.get(node_id, [])]
            else:
                return [(c, "company") for c in inv_to_comp.get(node_id, [])]

        start = (id_a, type_a)
        goal = (id_b, type_b)
        queue: List[List[tuple[str, str]]] = [[start]]
        paths = []
        visited = set([start])

        while queue and len(paths) < max_paths:
            path = queue.pop(0)
            if len(path) > 5:  # depth 4 edges => 5 nodes
                continue
            last_id, last_t = path[-1]
            if (last_id, last_t) == goal and len(path) >= 2:
                paths.append(path)
                continue
            for nxt in neighbors(last_id, last_t):
                if nxt in path:  # éviter cycles
                    continue
                new_path = path + [nxt]
                queue.append(new_path)
        # formatage
        out = []
        for p in paths[:max_paths]:
            out.append({"nodes": [{"id": nid, "type": nt} for nid, nt in p]})
        return out

    def _paths_company_company(self, a: str, b: str, year_min, year_max, currency, max_paths: int):
        # 1 saut : investisseur commun (company->investments->investors)
        res_a = self._filter_investments({"terms": {"companies": [a]}}, year_min, year_max, currency)
        res_b = self._filter_investments({"terms": {"companies": [b]}}, year_min, year_max, currency)
        inv_a: Set[str] = set()
        inv_b: Set[str] = set()
        inv_docs: Dict[str, Dict[str, Any]] = {}
        for r in res_a.get("hits", {}).get("hits", []) or []:
            s = r.get("_source", {})
            for iv in s.get("investors", []) or []:
                inv_a.add(iv)
                inv_docs.setdefault(iv, []).append(s)
        for r in res_b.get("hits", {}).get("hits", []) or []:
            s = r.get("_source", {})
            for iv in s.get("investors", []) or []:
                inv_b.add(iv)
                inv_docs.setdefault(iv, []).append(s)
        common = list(inv_a.intersection(inv_b))[:max_paths]
        paths = []
        for iv in common:
            docs = inv_docs.get(iv, [])[:2]
            paths.append({
                "type": "company-company",
                "via_investor": iv,
                "investments": docs,
            })
        return paths

    def _paths_company_investor(self, company_id: str, investor_id: str, year_min, year_max, currency, max_paths: int):
        res = self._filter_investments({"bool": {"filter": [
            {"terms": {"companies": [company_id]}},
            {"terms": {"investors": [investor_id]}}
        ]}}, year_min, year_max, currency, size=max_paths)
        hits = res.get("hits", {}).get("hits", []) or []
        return [{
            "type": "company-investor",
            "via_investment": h.get("_source", {})
        } for h in hits]

    def _paths_investor_investor(self, ia: str, ib: str, year_min, year_max, currency, max_paths: int):
        res_a = self._filter_investments({"terms": {"investors": [ia]}}, year_min, year_max, currency)
        res_b = self._filter_investments({"terms": {"investors": [ib]}}, year_min, year_max, currency)
        comp_a: Set[str] = set()
        comp_b: Set[str] = set()
        inv_docs: Dict[str, Dict[str, Any]] = {}
        for r in res_a.get("hits", {}).get("hits", []) or []:
            s = r.get("_source", {})
            for c in s.get("companies", []) or []:
                comp_a.add(c)
                inv_docs.setdefault(c, []).append(s)
        for r in res_b.get("hits", {}).get("hits", []) or []:
            s = r.get("_source", {})
            for c in s.get("companies", []) or []:
                comp_b.add(c)
                inv_docs.setdefault(c, []).append(s)
        common = list(comp_a.intersection(comp_b))[:max_paths]
        paths = []
        for c in common:
            docs = inv_docs.get(c, [])[:2]
            paths.append({
                "type": "investor-investor",
                "via_company": c,
                "investments": docs
            })
        return paths

    def _find_paths_between_entities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        a = params.get("entity_a")
        b = params.get("entity_b")
        type_a = (params.get("type_a") or "").lower()
        type_b = (params.get("type_b") or "").lower()
        if not (a and b and type_a in {"company", "investor"} and type_b in {"company", "investor"}):
            return {"error": "need entity_a/entity_b and type_a/type_b in {company, investor}"}

        year_min = params.get("year_min")
        year_max = params.get("year_max")
        currency = params.get("currency_code")
        max_paths = int(params.get("max_paths", 10))

        id_a = self._resolve_id(a, type_a)
        id_b = self._resolve_id(b, type_b)
        if not id_a or not id_b:
            return {"error": "could not resolve entity ids", "entity_a": id_a, "entity_b": id_b}

        paths: List[Dict[str, Any]] = []
        if type_a == "company" and type_b == "company":
            paths = self._paths_company_company(id_a, id_b, year_min, year_max, currency, max_paths)
        elif type_a == "company" and type_b == "investor":
            paths = self._paths_company_investor(id_a, id_b, year_min, year_max, currency, max_paths)
        elif type_a == "investor" and type_b == "company":
            paths = self._paths_company_investor(id_b, id_a, year_min, year_max, currency, max_paths)
        elif type_a == "investor" and type_b == "investor":
            paths = self._paths_investor_investor(id_a, id_b, year_min, year_max, currency, max_paths)

        # Si pas trouvé en 1-2 sauts, tenter BFS jusqu'à profondeur 4
        if len(paths) < max_paths:
            bfs_paths = self._bfs_paths_depth4(id_a, type_a, id_b, type_b, year_min, year_max, currency, max_paths - len(paths))
            paths.extend(bfs_paths)

        return {"summary": f"{len(paths)} chemins trouvés.", "paths": paths[:max_paths]}

    def run(self, task: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if task == "join":
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

            fb = self._fallback(parent_index, es_query, size)
            fb["note"] = "join returned 0 results"
            return fb

        if task == "find_paths_between_entities":
            return self._find_paths_between_entities(params or {})

        return {"error": f"unsupported task '{task}'", "supported": sorted(self.SUPPORTED)}
