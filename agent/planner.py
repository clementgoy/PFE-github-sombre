import json
from typing import Optional
from openai import OpenAI
from .planning_schema import Plan


def build_plan(user_message: str, model: str = "gpt-4o-mini", temperature: float = 0.0, timeout: int = 30) -> Plan:
    """
    Appelle le LLM (sans outils) pour produire un plan JSON conforme au schéma Plan.
    """
    client = OpenAI()
    system = (
        "Tu es un planificateur d'actions pour un système multi-agent.\n"
        "Tu dois produire uniquement un JSON conforme au schéma Plan.\n"
        "Actions possibles: FIND_PATHS, GRAPH_QUERY, CALL_SPECIALIST, ASK_CLARIFICATION, UNKNOWN.\n"
        "Si la requête porte sur des chemins/liaisons entre entités, choisis FIND_PATHS et remplis find_paths "
        "(depth par défaut 4, max_paths par défaut 10). Depth bornée 1-4.\n"
        "Si une entité ou des infos manquent/ambigües, choisis ASK_CLARIFICATION avec une question précise.\n"
        "Ne produis rien d'autre que le JSON du plan."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_message},
    ]
    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature, timeout=timeout
    )
    txt = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(txt)
    except Exception:
        # tentative simple de fallback : chercher le premier bloc JSON
        start = txt.find("{")
        end = txt.rfind("}")
        if start != -1 and end != -1:
            data = json.loads(txt[start:end+1])
        else:
            data = {"action": "UNKNOWN"}
    # validation Pydantic (borne depth/max_paths etc.)
    plan = Plan.parse_obj(data)
    return plan
