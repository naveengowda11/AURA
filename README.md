# AURA — AI Health Early-Warning & Future Risk Intelligence
Prototype for health-risk awareness and decision support. Not a diagnosis.

## Run
    cd backend && pip install -r requirements.txt
    uvicorn main:app --reload        # http://localhost:8000  (API docs: /docs)
Data is stored in `backend/aura.db` (SQLite; override with `AURA_DB=/path/aura.db`).

## Real use
Sign up -> log 10+ days (or import CSV: date,rhr,sleep,steps,weight,stress[,water,sbp,glucose]) -> AURA learns *your* baseline from your first ~15 entries, then scores drift, explains it and simulates habit changes. Account + data can be deleted in-app. "View sample data" shows 3 synthetic profiles.

## Deploy (Render/Railway/Fly)
Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT` (root dir `backend`). Attach a persistent disk and set AURA_DB to it. Serve over HTTPS.

## Real-data validation
Public datasets in `backend/data/` (Pima diabetes, UCI Cleveland heart disease) train two sub-models that feed the Metabolic and Cardiovascular scores; cross-validated AUC is shown in-app (GET /api/model-card). Probabilities are prior-shifted to an assumed population prevalence.

## Extras
Symptom check-in (voice/text, POST /api/checkin), confidence indicator, urgent-reading safety banner, Save-as-PDF summary.

## Devices (no manual logging)
Status as of Nov 2026 (checked against Google's docs): Google Fit REST APIs end with 2026 and take no new sign-ups; the Fitbit Web API was switched off on 2 Nov 2026; the replacement is the **Google Health API** (cloud, Pixel Watch/Fitbit, Google OAuth). **Health Connect** is on-device Android only, so it needs an app on the phone.
1. **Universal sync token** - Account > Connect your devices > Create token. Any phone/watch app or script POSTs daily summaries to `POST /api/ingest/daily` with `Authorization: Bearer aura_dev_...`:
   `{"records":[{"date":"2026-11-24","rhr":62,"sleep_hours":7.2,"steps":8400,"weight_kg":70,"sbp":118,"glucose_mgdl":92}],"source":"my-app"}`
   All fields except `date` are optional; newest non-empty value wins; implausible values are rejected. Works with Health Connect-to-webhook sync apps, iOS Shortcuts / auto-export apps, Tasker.
2. **Apple Watch / iPhone** - `python tools/import_apple_health.py export.zip --server http://localhost:8000 --token aura_dev_XXXX` (use `--dry-run` first). Parsed on your machine; only daily summaries are sent.
3. **Google Health API** - set the `GOOGLE_HEALTH_*` variables, then Connect > Sync now (last 30 days: steps, sleep, resting HR). Google marks these scopes Restricted: it works for accounts you authorise while developing; public launch needs Google's app verification. Verified against the docs: steps (dailyRollUp), sleep (reconcile, main sleep). **Resting HR parsing is best-effort** (field names were not in the docs I could read) and a failure is reported, not hidden. Not tested against live Google (no credentials in my environment).
Missing signals (stress is not measured by watches; weight needs a smart scale) get neutral assumed values and the app says which. Native Android Health Connect companion app is not included.

## Action plan & lab reports
GET /api/plan/{profile|me}: habit changes ranked by estimated index reduction (each scored with the same engine as Future You) with a combined estimate. Lab upload: POST /api/report/extract (PDF text via pypdf, scans/photos via Claude vision with ANTHROPIC_API_KEY; user verifies values) then POST /api/me/labs. GET /api/report/sample for a demo report.

## Languages
Picker in the nav: English, Hindi, Kannada, Tamil, Telugu (built-in text, work offline) plus Bengali, Marathi, Gujarati, Malayalam, Punjabi via live translation (`POST /api/translate`, Claude API, cached in SQLite). Set `ANTHROPIC_API_KEY` in `backend/.env` (see `.env.example`). Dynamic text (story, answers, summary), typed/spoken check-ins and questions are translated both ways. Voice input uses the selected language. Have native speakers review medical wording before real use.

## Honest limits
Population model labels come from a clinically-inspired synthetic function (not real patient outcomes) — replace in `train()` with a real dataset. Not HIPAA/GDPR-audited. Not a medical device.
