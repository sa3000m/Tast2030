# Soil Stabilization Calculator (Streamlit Cloud Ready)

Professional bilingual (Arabic/English) soil stabilization calculator with lead capture and PDF quotations.

## Features
- Input area in m²
- Quantity based on 52 m²/ton at 4 cm baseline
- Thickness selector (4 cm default)
- Output:
  - Total tons needed
  - Estimated cost (default 4,000 AED/ton)
- WhatsApp share button
- PDF quotation download
- Lead saving to SQLite (when writable)

## 1) Local setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run budget_app.py
```

## 2) Streamlit Cloud deployment
1. Push this repo to GitHub.
2. On Streamlit Cloud, create a new app:
   - **Main file path:** `budget_app.py`
3. Add optional secrets (App settings → Secrets):
```toml
DEFAULT_THICKNESS_CM = 4
AREA_PER_TON_AT_DEFAULT = 52
PRICE_PER_TON_AED = 4000
WHATSAPP_NUMBER_E164 = "971557100040"
LEADS_DB_PATH = "leads.db"
```
4. Deploy.

### Important Streamlit Cloud note
- Streamlit Cloud filesystem is ephemeral. SQLite data may reset on redeploy/restart.
- For persistent leads, use a managed DB (e.g., Supabase/Postgres) or Google Sheets integration.

## 3) Docker deployment
```bash
docker build -t soil-calculator:latest .
docker run -p 8501:8501 -v $(pwd)/data:/app -e LEADS_DB_PATH=/app/data/leads.db soil-calculator:latest
```

## Environment configuration
- `DEFAULT_THICKNESS_CM` (default `4`)
- `AREA_PER_TON_AT_DEFAULT` (default `52`)
- `PRICE_PER_TON_AED` (default `4000`)
- `WHATSAPP_NUMBER_E164` (default `971557100040`)
- `LEADS_DB_PATH` (default `leads.db`)
