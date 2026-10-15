# MGP Stats

Serveur léger qui récupère les données MotoGP (calendrier, séances, classements, résultats) et les expose en JSON minimal pour ESP32.

## Stack

- **Python 3.13+** / **FastAPI**
- **httpx** (appels async vers l'API MotoGP)
- **Docker** / **Docker Compose**

## Démarrage rapide

```bash
docker compose up -d
# ou en local :
source .venv/bin/activate
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

## API

| Endpoint | Description |
|---|---|
| `GET /api/v1/calendar` | Calendrier complet |
| `GET /api/v1/next` | Prochain GP |
| `GET /api/v1/sessions?round=N` | Séances d'un GP |
| `GET /api/v1/standings?category=MotoGP` | Classement pilotes |
| `GET /api/v1/results/race?round=N` | Résultats course |
| `GET /api/v1/health` | Santé |

Documentation complète dans [`API.md`](API.md) et sur `http://localhost:8000/docs`.

## Structure

```
.
├── Dockerfile
├── docker-compose.yml
├── server/
│   ├── main.py          # Routes FastAPI
│   ├── gp_client.py     # Appels API MotoGP
│   └── cache.py         # Cache TTL 15 min
├── tests/
│   └── test_api.py
└── .github/workflows/ci.yml
```