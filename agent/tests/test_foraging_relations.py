from agent.agents.foraging import ForagingAgent
from agent.agents.relations import RelationsAgent


def test_foraging_lookup_company():
    def es_post(path, json=None, **kwargs):
        assert path == "/company/_search"
        return {
            "hits": {
                "total": {"value": 2},
                "hits": [{"_source": {"id": "c1"}}, {"_source": {"id": "c2"}}],
            }
        }

    agent = ForagingAgent(lambda *a, **k: {}, es_post)
    res = agent.run("lookup_company", {"label": "test", "size": 5})
    assert "2 résultats" in res["summary"]
    assert len(res["items"]) == 2


def test_relations_join_fallback():
    # Join returns 0, fallback returns lookup results
    def es_post(path, json=None, **kwargs):
        if path.startswith("/siren/parent/_search"):
            return {"hits": {"total": {"value": 0}, "hits": []}}
        if path.startswith("/parent/_search"):
            return {
                "hits": {
                    "total": {"value": 3},
                    "hits": [{"_source": {"id": "p1"}}, {"_source": {"id": "p2"}}],
                }
            }
        raise AssertionError(f"unexpected path {path}")

    agent = RelationsAgent(lambda *a, **k: {}, es_post)
    res = agent.run("join", {"parent_index": "parent", "child_index": "child", "on": ["a", "b"], "size": 5})
    assert "Fallback lookup" in res["summary"]
    assert len(res["items"]) == 2

