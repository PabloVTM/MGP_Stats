# MGP Stats

Serveur léger qui récupère les données MotoGP (calendrier, prochain GP, classements) et les expose en JSON minimal pour ESP32.

## Stack

- **Python 3.13+** / **FastAPI**
- **httpx** (appels async vers l'API MotoGP)
- **Docker** / **Docker Compose**

## Démarrage rapide

```bash
MGP_DOCKER_USERNAME=<votre-user> docker compose up -d
# ou en local :
source .venv/bin/activate
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

## API

| Endpoint | Description |
|---|---|
| `GET /api/v1/calendar?year=N` | Calendrier complet de la saison |
| `GET /api/v1/next?year=N` | Prochain GP (bascule sur N+1 hors saison) |
| `GET /api/v1/standings?year=N` | Classement pilotes MotoGP |
| `GET /api/v1/health` | Santé (exclue du rate limit) |

Le paramètre `year` est optionnel (défaut : année courante, plage 1949–2100).
Rate limit : **30 requêtes/min par IP** (429 au-delà).

Documentation complète dans [`API.md`](API.md). La doc interactive `/docs` est
désactivée par défaut — l'activer avec `MGP_ENABLE_DOCS=true`.

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `MGP_API_URL` | `https://api.pulselive.motogp.com/motogp/v1` | API source |
| `MGP_API_KEY` | (vide) | Clé d'API si fournisseur alternatif |
| `MGP_ENABLE_DOCS` | (vide = off) | Expose `/docs` et `/openapi.json` |

## Avertissements

- **API amont non contractuelle** : les données proviennent de l'API publique du
  site motogp.com, sans garantie de disponibilité ni d'autorisation d'usage
  intensif. Un blocage côté fournisseur est possible.
- **HTTP uniquement** : prévu pour un usage sur réseau local (ESP32).
- **Reverse proxy de confiance requis** : le rate limit s'appuie sur
  `X-Forwarded-For`. Derrière un proxy de confiance (Traefik/WAF) c'est fiable,
  mais **n'exposez pas le conteneur directement** : l'en-tête serait spoofable
  pour contourner le rate limit.

## Tests & CI

```bash
pytest tests/ -v   # 100 % offline, API MotoGP mockée
```

Le workflow GitHub Actions exécute lint (ruff), tests et audit des dépendances
(pip-audit) sur chaque push, puis build l'image Docker, la scanne avec Trivy et
ne la pousse vers Docker Hub que si elle est saine (branches `main`,
`develop/*`, `hotfix/*`, `refactor/*` et tags).

## Structure

```
.
├── Dockerfile
├── docker-compose.yml
├── server/
│   ├── main.py          # Routes FastAPI
│   ├── gp_client.py     # Appels API MotoGP (retry, client partagé)
│   ├── cache.py         # Cache TTL borné (1h week-end / 24h semaine)
│   └── rate_limit.py    # Rate limit 30 req/min par IP
├── tests/
│   └── test_api.py
└── .github/workflows/ci.yml
```
