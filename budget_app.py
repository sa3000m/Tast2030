import io
import math
import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def get_setting(name: str, default, cast):
    secret_val = st.secrets.get(name) if hasattr(st, "secrets") else None
    raw = secret_val if secret_val is not None else os.getenv(name, default)
    return cast(raw)


DEFAULT_THICKNESS_CM = get_setting("DEFAULT_THICKNESS_CM", "4", int)
AREA_PER_TON_AT_DEFAULT = get_setting("AREA_PER_TON_AT_DEFAULT", "52", float)
PRICE_PER_TON_AED = get_setting("PRICE_PER_TON_AED", "4000", float)
WHATSAPP_NUMBER_E164 = str(get_setting("WHATSAPP_NUMBER_E164", "971557100040", str))
DB_PATH = Path(get_setting("LEADS_DB_PATH", "leads.db", str))
THICKNESS_OPTIONS = [2, 3, 4, 5, 6, 8, 10]

st.set_page_config(page_title="Soil Stabilization Calculator", page_icon="🏗️", layout="centered")

st.markdown(
    """
    <style>
      .stApp {background: radial-gradient(circle at top, #1f2937 0%, #0b1220 45%, #05080f 100%);color: #f8fafc;}
      .main-card {background: rgba(15, 23, 42, 0.78);border: 1px solid rgba(212, 175, 55, 0.35);box-shadow: 0 12px 32px rgba(0,0,0,0.35);border-radius: 20px;padding: 1.2rem;}
      .metric {padding: 0.9rem;border-radius: 14px;background: linear-gradient(135deg, rgba(212,175,55,0.14), rgba(255,255,255,0.03));border: 1px solid rgba(212,175,55,0.32);margin-bottom: 0.8rem;}
      .gold {color: #facc15;font-weight: 700;} .subtitle {color: #cbd5e1;font-size: 0.95rem;} .small {color: #94a3b8;font-size: 0.85rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def init_db() -> str | None:
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(DB_PATH)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    area_m2 REAL NOT NULL,
                    thickness_cm REAL NOT NULL,
                    tons_needed REAL NOT NULL,
                    estimated_cost_aed REAL NOT NULL
                )
                """
            )
            conn.commit()
        return None
    except Exception as exc:
        return str(exc)


def valid_phone(phone: str) -> bool:
    return bool(re.fullmatch(r"[0-9+()\-\s]{7,20}", phone.strip()))


def save_lead(name: str, phone: str, area_m2: float, thickness_cm: float, tons: float, cost: float) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """
            INSERT INTO leads (created_at, name, phone, area_m2, thickness_cm, tons_needed, estimated_cost_aed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (datetime.now(timezone.utc).isoformat(), name, phone, area_m2, thickness_cm, tons, cost),
        )
        conn.commit()


def make_pdf_quote(lang: str, name: str, phone: str, area: float, thickness: float, tons: float, cost: float) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    _, height = A4
    y = height - 60

    title = "Soil Stabilization Quotation" if lang == "English" else "عرض سعر تثبيت التربة"
    pdf.setTitle("Soil Stabilization Quotation")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, title)

    y -= 30
    pdf.setFont("Helvetica", 11)
    for line in [
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Client Name: {name}",
        f"Phone: {phone}",
        f"Area (m2): {area:,.2f}",
        f"Thickness (cm): {thickness:g}",
        f"Total Tons Needed: {tons:,.2f}",
        f"Estimated Cost (AED): {cost:,.2f}",
        f"Unit Price (AED/ton): {PRICE_PER_TON_AED:,.2f}",
    ]:
        pdf.drawString(50, y, line)
        y -= 20

    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawString(50, y - 10, "Estimate only. Final quotation is subject to site inspection and final agreement.")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.read()


db_init_error = init_db()

translations = {
    "English": {
        "title": "🏗️ Soil Stabilization Calculator",
        "subtitle": "Estimate material quantity and project cost in seconds.",
        "lead": "Lead details",
        "name": "Name",
        "phone": "Phone",
        "area": "Area (m²)",
        "thickness": "Thickness (cm)",
        "results": "Results",
        "tons": "Total tons needed",
        "cost": "Estimated cost (AED)",
        "save": "Save lead",
        "saved": "Lead saved successfully.",
        "invalid": "Please enter a valid name, phone, and area.",
        "db_warning": "Lead storage is unavailable in this deployment. You can still calculate and download PDF.",
        "wa": "Send result on WhatsApp",
        "pdf": "Download PDF quotation",
    },
    "العربية": {
        "title": "🏗️ حاسبة تثبيت التربة",
        "subtitle": "احسب الكمية والتكلفة التقديرية خلال ثوانٍ.",
        "lead": "بيانات العميل",
        "name": "الاسم",
        "phone": "رقم الهاتف",
        "area": "المساحة (م²)",
        "thickness": "السماكة (سم)",
        "results": "النتائج",
        "tons": "إجمالي الأطنان المطلوبة",
        "cost": "التكلفة التقديرية (درهم)",
        "save": "حفظ العميل",
        "saved": "تم حفظ بيانات العميل بنجاح.",
        "invalid": "الرجاء إدخال اسم ورقم هاتف ومساحة صحيحة.",
        "db_warning": "حفظ العملاء غير متاح في هذا النشر حالياً. يمكنك الاستمرار في الحساب وتحميل PDF.",
        "wa": "إرسال النتيجة عبر واتساب",
        "pdf": "تحميل عرض السعر PDF",
    },
}

lang = st.selectbox("Language / اللغة", options=["English", "العربية"], index=1)
t = translations[lang]

st.markdown('<div class="main-card">', unsafe_allow_html=True)
st.title(t["title"])
st.markdown(f'<p class="subtitle">{t["subtitle"]}</p>', unsafe_allow_html=True)

if db_init_error:
    st.warning(t["db_warning"])

st.subheader(t["lead"])
col1, col2 = st.columns(2)
with col1:
    name = st.text_input(t["name"], max_chars=80)
with col2:
    phone = st.text_input(t["phone"], max_chars=20)

area_m2 = st.number_input(t["area"], min_value=0.0, value=1000.0, step=10.0)
thickness_cm = st.select_slider(t["thickness"], options=THICKNESS_OPTIONS, value=DEFAULT_THICKNESS_CM)

coverage = AREA_PER_TON_AT_DEFAULT * (DEFAULT_THICKNESS_CM / thickness_cm)
tons_needed = math.ceil((area_m2 / coverage if coverage > 0 else 0) * 100) / 100
estimated_cost = tons_needed * PRICE_PER_TON_AED

st.subheader(t["results"])
st.markdown(f'<div class="metric"><span class="small">{t["tons"]}</span><br><span class="gold">{tons_needed:,.2f} ton</span></div>', unsafe_allow_html=True)
st.markdown(f'<div class="metric"><span class="small">{t["cost"]}</span><br><span class="gold">AED {estimated_cost:,.2f}</span></div>', unsafe_allow_html=True)

if st.button(t["save"], disabled=bool(db_init_error)):
    if name.strip() and valid_phone(phone) and area_m2 > 0:
        save_lead(name.strip(), phone.strip(), area_m2, float(thickness_cm), tons_needed, estimated_cost)
        st.success(t["saved"])
    else:
        st.warning(t["invalid"])

message = (
    f"{t['title']}\n"
    f"{t['area']}: {area_m2:,.2f}\n"
    f"{t['thickness']}: {thickness_cm} cm\n"
    f"{t['tons']}: {tons_needed:,.2f}\n"
    f"{t['cost']}: AED {estimated_cost:,.2f}"
)
st.link_button(t["wa"], f"https://wa.me/{WHATSAPP_NUMBER_E164}?text={quote(message)}")

st.download_button(
    label=t["pdf"],
    data=make_pdf_quote(lang, name or "N/A", phone or "N/A", area_m2, float(thickness_cm), tons_needed, estimated_cost),
    file_name=f"soil_quote_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
    mime="application/pdf",
)

st.markdown('</div>', unsafe_allow_html=True)
