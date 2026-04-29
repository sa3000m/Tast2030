# Ultra Luxury Soil Stabilization Calculator (Streamlit Cloud Ready)

An Arabic-first luxury landing page + calculator + lead generation app.

## Highlights
- Premium Arabic hero and sales funnel flow
- Bilingual (Arabic/English) switch
- Preliminary estimate calculator (tons + cost)
- WhatsApp CTA with professional Arabic message
- PDF quotation export
- Lead saving in SQLite (works where filesystem is writable)
- Streamlit Cloud compatible (`st.secrets` + env fallback)

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run budget_app.py
```

## Streamlit Cloud setup
1. Push repo to GitHub.
2. Deploy on Streamlit Cloud with main file: `budget_app.py`.
3. (Optional) Add secrets:
```toml
DEFAULT_THICKNESS_CM = 4
AREA_PER_TON_AT_DEFAULT = 52
PRICE_PER_TON_AED = 4000
WHATSAPP_NUMBER_E164 = "971557100040"
LEADS_DB_PATH = "leads.db"
```

## Notes
- Pricing language is shown as **preliminary estimate**.
- Final note included: "السعر النهائي يعتمد على معاينة الموقع وتجهيز الأرض."
- On Streamlit Cloud, SQLite may reset after restarts/redeploys.
