# siren-mvp

MVP d'agent conversationnel d'enquête : FastAPI + LLM orchestrateur + requêtes Elasticsearch/Federate sur un jeu `company/investment/investor`. L'endpoint `/chat` délègue les tâches métier au `SpecialistAgent`.

## Prérequis
- Python 3.10+ (testé sur Ubuntu)
- Siren / Elasticsearch accessibles (ex : `https://localhost:9220`)
- `pip install -r requirements.txt` (inclut `python-dateutil` requis par `SpecialistAgent`)

## Configuration (variables d'env)
- `ES_URL` (ex: `https://localhost:9220`)
- `ES_USER` / `ES_PASS`
- `ES_VERIFY` (`true`|`false`, par défaut `false`)
- `GRAPH_AGENT_TOKEN` (ex: `devtoken`, utilisé dans le header `Authorization: Bearer ...`)
- `OPENAI_API_KEY`, `OPENAI_MODEL` (ex: `gpt-4o-mini`)
- `CHAT_MODE` (`llm` par défaut, `local` pour un fallback sans OpenAI)

## Démarrage (Ubuntu)
```bash
cd PFE-github-sombre
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ES_URL="https://localhost:9220"
export ES_USER="sirenadmin"
export ES_PASS="password"
export ES_VERIFY="false"
export GRAPH_AGENT_TOKEN="devtoken"
export OPENAI_API_KEY="votre_cle"
export OPENAI_MODEL="gpt-4o-mini"
uvicorn agent.app:app --reload --port 8000
```

## Sanity check
```bash
curl -H "Authorization: Bearer devtoken" http://127.0.0.1:8000/health
curl -H "Authorization: Bearer devtoken" http://127.0.0.1:8000/graph/indices
```

## Exemple `/chat`
```bash
curl -H "Authorization: Bearer devtoken" \
     -H "Content-Type: application/json" \
     -d @requests/investissements.json \
     http://127.0.0.1:8000/chat
```

## Notes
- En l'absence de clé OpenAI, définir `CHAT_MODE=local` pour un mini-plan local.
- Les autres agents (foraging, relations, structuring, etc.) sont pour l'instant des squelettes.
