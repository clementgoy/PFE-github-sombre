from agent.agents.relations import RelationsAgent


def test_find_paths_company_company():
    # Mock ES responses:
    # - company lookup by label
    # - investments for company A and B
    # - investors overlap: inv1 commun
    def es_post(path, json=None, **kwargs):
        if path == "/company/_search":
            # return id for label match
            q = json.get("query", {})
            if "term" in q and "label" in q["term"]:
                val = q["term"]["label"]
                if val == "A": return {"hits": {"hits": [{"_source": {"id": "company/a"}}]}}
                if val == "B": return {"hits": {"hits": [{"_source": {"id": "company/b"}}]}}
            if "term" in q and "label.raw" in q["term"]:
                val = q["term"]["label.raw"]
                if val == "A": return {"hits": {"hits": [{"_source": {"id": "company/a"}}]}}
                if val == "B": return {"hits": {"hits": [{"_source": {"id": "company/b"}}]}}
            return {"hits": {"hits": []}}
        if path == "/investment/_search":
            # filter on companies: produce different investor sets
            filters = json.get("query", {}).get("bool", {}).get("filter", [])
            companies = None
            for f in filters:
                if "terms" in f and "companies" in f["terms"]:
                    companies = f["terms"]["companies"]
            if companies == ["company/a"]:
                return {"hits": {"hits": [
                    {"_source": {"companies": ["company/a"], "investors": ["inv1"], "funded_year": 2011}},
                ]}}
            if companies == ["company/b"]:
                return {"hits": {"hits": [
                    {"_source": {"companies": ["company/b"], "investors": ["inv1", "inv2"], "funded_year": 2012}},
                ]}}
            return {"hits": {"hits": []}}
        raise AssertionError(f"unexpected path {path}")

    agent = RelationsAgent(lambda *a, **k: {}, es_post)
    res = agent.run("find_paths_between_entities", {
        "entity_a": "A", "type_a": "company",
        "entity_b": "B", "type_b": "company",
        "max_paths": 5
    })
    assert res["summary"].startswith("1 chemins")
    assert len(res["paths"]) == 1
    assert res["paths"][0]["via_investor"] == "inv1"


def test_bfs_depth4():
    # Graph : cA - i1 - cB - i2 - cC (depth 4 nodes)
    def es_post(path, json=None, **kwargs):
        if path == "/company/_search":
            q = json.get("query", {})
            if "term" in q and "label" in q["term"]:
                val = q["term"]["label"]
                if val == "A": return {"hits": {"hits": [{"_source": {"id": "cA"}}]}}
                if val == "C": return {"hits": {"hits": [{"_source": {"id": "cC"}}]}}
            if "term" in q and "label.raw" in q["term"]:
                val = q["term"]["label.raw"]
                if val == "A": return {"hits": {"hits": [{"_source": {"id": "cA"}}]}}
                if val == "C": return {"hits": {"hits": [{"_source": {"id": "cC"}}]}}
            return {"hits": {"hits": []}}
        if path == "/investment/_search":
            # return a set of investments with company/investor links
            return {
                "hits": {
                    "hits": [
                        {"_source": {"companies": ["cA"], "investors": ["i1"], "funded_year": 2010}},
                        {"_source": {"companies": ["cB"], "investors": ["i1", "i2"], "funded_year": 2011}},
                        {"_source": {"companies": ["cC"], "investors": ["i2"], "funded_year": 2012}},
                    ]
                }
            }
        raise AssertionError(f"unexpected path {path}")

    agent = RelationsAgent(lambda *a, **k: {}, es_post)
    res = agent.run("find_paths_between_entities", {
        "entity_a": "A", "type_a": "company",
        "entity_b": "C", "type_b": "company",
        "max_paths": 5
    })
    assert res["paths"], "expected at least one path"
    # One of the paths should go cA -> i1 -> cB -> i2 -> cC
    nodes = res["paths"][0]["nodes"]
    ids = [n["id"] for n in nodes]
    assert ids == ["cA", "i1", "cB", "i2", "cC"]
