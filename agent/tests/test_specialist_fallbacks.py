import pytest

from agent.agents.specialist import SpecialistAgent


def test_investments_by_amount_fallback():
    # join returns zero, lookup investment returns two hits, lookup company resolves labels
    def es_post(path, json=None, **kwargs):
        if path.startswith("/siren/company/_search"):
            return {"hits": {"total": {"value": 0}, "hits": []}}
        if path.startswith("/investment/_search"):
            return {
                "hits": {
                    "total": {"value": 2},
                    "hits": [
                        {"_source": {"companies": ["company/a", "company/b"], "raised_amount": 2_000_000}},
                        {"_source": {"companies": ["company/a"], "raised_amount": 3_000_000}},
                    ],
                }
            }
        if path.startswith("/company/_search"):
            return {
                "hits": {
                    "hits": [
                        {"_source": {"id": "company/a", "label": "A"}},
                        {"_source": {"id": "company/b", "label": "B"}},
                    ]
                }
            }
        raise AssertionError(f"unexpected path {path}")

    agent = SpecialistAgent(lambda *a, **k: {}, es_post)
    res = agent.investments_by_amount({"min_amount": 1_000_000, "join_company": True})
    assert "fallback" in res["summary"]
    assert len(res["companies"]) == 2
    assert res["companies"][0]["company_label"] in {"A", "B"}


def test_company_investors_fallback():
    # join returns zero; investments carry investors; lookup investor resolves labels
    def es_post(path, json=None, **kwargs):
        if path.startswith("/siren/investor/_search"):
            return {"hits": {"total": {"value": 0}, "hits": []}}
        if path.startswith("/investment/_search"):
            return {
                "hits": {
                    "hits": [
                        {"_source": {"investors": ["investor/1", "investor/2"]}},
                        {"_source": {"investors": ["investor/2"]}},
                    ]
                }
            }
        if path.startswith("/investor/_search"):
            return {
                "hits": {
                    "hits": [
                        {"_source": {"id": "investor/1", "label": "INV1"}},
                        {"_source": {"id": "investor/2", "label": "INV2"}},
                    ]
                }
            }
        if path.startswith("/company/_search"):
            return {"hits": {"hits": [{"_source": {"id": "company/a"}}]}}
        raise AssertionError(f"unexpected path {path}")

    agent = SpecialistAgent(lambda *a, **k: {}, es_post)
    res = agent.company_investors({"company_id": "company/a"})
    assert "fallback" in res["summary"]
    assert len(res["investors"]) == 2
    labels = {i["investor_label"] for i in res["investors"]}
    assert labels == {"INV1", "INV2"}

