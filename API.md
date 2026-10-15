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

---

## Calendrier

```
GET /api/v1/calendar?year=2026
```

| Param | Type | Défaut |
|---|---|---|
| `year` | int | année courante |

```json
{
  "cal": [
    {
      "rnd": 1,
      "name": "Qatar Grand Prix",
      "short": "QAT",
      "date": "2026-03-08"
    }
  ]
}
```

| Champ | Description |
|---|---|
| `rnd` | Numéro du round |
| `name` | Nom du Grand Prix |
| `short` | Code court (QAT, SPA, ITA...) |
| `date` | Date de début |

---

## Prochain GP

```
GET /api/v1/next?year=2026
```

```json
{
  "next": { "rnd": 3, "name": "Spanish Grand Prix", "short": "SPA", "date": "2026-04-19" }
}
```

---

## Séances d'un GP

```
GET /api/v1/sessions?round=N&category=MotoGP
```

| Param | Type | Défaut |
|---|---|---|
| `round` | int | **obligatoire** |
| `category` | string | `MotoGP` (MotoGP, Moto2, Moto3, MotoE) |

```json
{
  "sessions": [
    { "s": "fp1", "dt": "2026-03-08T09:00:00", "num": 1, "finished": true },
    { "s": "fp2", "dt": "2026-03-08T12:00:00", "num": 1, "finished": true },
    { "s": "fp3", "dt": "2026-03-09T08:00:00", "num": 1, "finished": true },
    { "s": "q1", "dt": "2026-03-09T10:00:00", "num": 1, "finished": true },
    { "s": "q2", "dt": "2026-03-09T13:00:00", "num": 1, "finished": true },
    { "s": "wup", "dt": "2026-03-10T08:00:00", "num": 1, "finished": false },
    { "s": "race", "dt": "2026-03-10T11:00:00", "num": 1, "finished": false }
  ]
}
```

| Clé `s` | Séance |
|---|---|
| `fp1`-`fp4` | Essais libres 1 à 4 |
| `q1`, `q2` | Qualifications |
| `race` | Course |
| `sprint` | Sprint |
| `sq1`, `sq2` | Qualifs sprint |
| `wup` | Warm-up |

---

## Classement pilotes

```
GET /api/v1/standings?category=MotoGP
```

| Param | Type | Défaut |
|---|---|---|
| `category` | string | `MotoGP` |

```json
{
  "drv": [
    { "pos": 1, "name": "Martin", "team": "Prima Pramac Racing", "pts": 508 },
    { "pos": 2, "name": "Bagnaia", "team": "Ducati Lenovo Team", "pts": 489 }
  ]
}
```

---

## Résultats d'une course

```
GET /api/v1/results/race?round=N&category=MotoGP
```

```json
{
  "res": [
    { "pos": 1, "name": "Martin", "num": 89, "team": "Prima Pramac Racing", "laps": 24, "time": "41:12.345" },
    { "pos": 2, "name": "Bagnaia", "num": 1, "team": "Ducati Lenovo Team", "laps": 24, "time": "+0.845" }
  ]
}
```

---

## Codes d'erreur

| Code | Signification |
|---|---|
| 200 | OK |
| 404 | Endpoint inconnu |
| 422 | Paramètre `round` manquant |
| 503 | API MotoGP amont injoignable |

---

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `MGP_API_URL` | `https://api.pulselive.motogp.com/motogp/v1` | API source |
| `MGP_API_KEY` | (vide) | Clé d'API si fournisseur alternatif |

---

## Swagger

Documentation interactive : `http://<serveur>:8000/docs`