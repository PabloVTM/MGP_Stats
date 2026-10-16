# API MotoGP Stats — Documentation

Base URL : `http://<serveur>:8000`

Toutes les réponses sont en JSON avec des clés courtes pour l'ESP32.

---

## Santé

```
GET /api/v1/health
```

```json
{
  "ok": true,
  "ts": "2026-10-15T12:00:00+00:00"
}
```

Exclue du rate limit.

---

## Calendrier

```
GET /api/v1/calendar?year=2026
```

| Param | Type | Défaut | Contrainte |
|---|---|---|---|
| `year` | int | année courante | 1949 – 2100 |

```json
{
  "cal": [
    {
      "rnd": 1,
      "name": "Qatar Grand Prix",
      "date": "2026-03-08"
    }
  ]
}
```

| Champ | Description |
|---|---|
| `rnd` | Numéro du round |
| `name` | Nom du Grand Prix |
| `date` | Date de la course (dimanche) |

---

## Prochain GP

```
GET /api/v1/next?year=2026
```

```json
{
  "next": { "rnd": 3, "name": "Spanish Grand Prix", "date": "2026-04-19" }
}
```

Sans paramètre `year`, si tous les GP de l'année en cours sont passés
(hors saison), l'endpoint retourne automatiquement le premier GP de l'année
suivante. Avec un `year` explicite dont tous les GP sont passés, il retourne
le dernier GP de cette année-là.

Un GP dont la date est le jour J reste le « prochain GP » jusqu'à minuit UTC.

---

## Classement pilotes

```
GET /api/v1/standings?year=2026
```

| Param | Type | Défaut | Contrainte |
|---|---|---|---|
| `year` | int | année courante | 1949 – 2100 |

Catégorie MotoGP uniquement.

```json
{
  "drv": [
    { "pos": 1, "name": "J. Martin", "pts": 355 },
    { "pos": 2, "name": "F. Bagnaia", "pts": 340 }
  ]
}
```

| Champ | Description |
|---|---|
| `pos` | Position au championnat |
| `name` | Nom abrégé (initiale du prénom + nom) |
| `pts` | Points |

---

## Codes d'erreur

| Code | Signification |
|---|---|
| 200 | OK |
| 404 | Endpoint inconnu |
| 422 | Paramètre invalide (ex. `year` hors plage) |
| 429 | Rate limit dépassé (30 req/min par IP) |
| 503 | API MotoGP amont injoignable |

Exemple de réponse 429 :

```json
{ "err": "rate_limit", "msg": "Trop de requêtes, réessaie dans quelques secondes" }
```

---

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `MGP_API_URL` | `https://api.pulselive.motogp.com/motogp/v1` | API source |
| `MGP_API_KEY` | (vide) | Clé d'API si fournisseur alternatif |
| `MGP_ENABLE_DOCS` | (vide = off) | Expose `/docs` et `/openapi.json` |

---

## Swagger

La documentation interactive `/docs` est **désactivée par défaut** en prod.
L'activer en définissant `MGP_ENABLE_DOCS=true`, puis :
`http://<serveur>:8000/docs`
