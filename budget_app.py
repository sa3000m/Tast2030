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

st.set_page_config(page_title="Soil Stabilization Calculator", page_icon="🏗️", layout="wide")
st.set_page_config(page_title="Soil Stabilization Calculator", page_icon="🏗️", layout="centered")

st.markdown(
    """
    <style>
      .stApp {background: radial-gradient(circle at top, #13211a 0%, #0b1220 40%, #06080f 100%);color: #f8fafc;}
      .rtl {direction: rtl; text-align: right;}
      .hero {background: linear-gradient(140deg, rgba(14,24,20,0.9), rgba(20,32,30,0.7));border:1px solid rgba(212,175,55,0.35);border-radius:24px;padding:2rem;box-shadow:0 20px 50px rgba(0,0,0,.35);margin-bottom:1.2rem;}
      .hero h1 {font-size: 2rem; line-height:1.4; color:#f8fafc; margin-bottom:0.6rem;}
      .hero p {color:#d1d5db; font-size:1.05rem; margin-bottom:1rem;}
      .pill {display:inline-block;padding:0.5rem 0.9rem;border-radius:999px;border:1px solid rgba(34,197,94,.5);color:#bbf7d0;background:rgba(34,197,94,.08);font-size:.86rem;}
      .premium-card {background: rgba(15, 23, 42, 0.78);border: 1px solid rgba(212, 175, 55, 0.35);border-radius: 18px;padding: 1.1rem;box-shadow: 0 10px 24px rgba(0,0,0,0.30);}
      .metric {padding: 0.95rem;border-radius: 14px;background: linear-gradient(135deg, rgba(212,175,55,0.14), rgba(34,197,94,0.12));border: 1px solid rgba(212,175,55,0.32);}
      .gold {color: #facc15;font-weight: 700;font-size:1.3rem;} .small {color:#cbd5e1;font-size:.9rem;}
      .section-title {font-size:1.45rem;color:#f8fafc;margin:1.3rem 0 .8rem 0;}
      .feature-grid {display:grid;grid-template-columns: repeat(auto-fit,minmax(180px,1fr));gap:0.8rem;}
      .feature {border:1px solid rgba(212,175,55,.25);padding:.8rem;border-radius:12px;background:rgba(15,23,42,.45);}
      .placeholder {min-height:170px;border:1px dashed rgba(212,175,55,.5);border-radius:16px;padding:1rem;background:rgba(2,6,23,.35);display:flex;align-items:center;justify-content:center;color:#cbd5e1;}
      .final-cta {margin-top:1.6rem;background:linear-gradient(120deg, rgba(180,83,9,.25), rgba(21,128,61,.25));padding:1.4rem;border-radius:18px;border:1px solid rgba(250,204,21,.35);}
      .small-note {color:#9ca3af;font-size:.9rem;}
      @media (max-width: 768px){ .hero h1 {font-size:1.45rem;} }
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
                """CREATE TABLE IF NOT EXISTS leads (
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
                )"""
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
            """INSERT INTO leads (created_at, name, phone, area_m2, thickness_cm, tons_needed, estimated_cost_aed)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
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
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "Soil Stabilization Quotation" if lang == "English" else "عرض سعر تثبيت التربة")
    y -= 30
    pdf.setFont("Helvetica", 11)
    lines = [

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
        f"Estimated Tons: {tons:,.2f}",
        f"Preliminary Cost Estimate (AED): {cost:,.2f}",
        "Final price depends on site inspection and ground preparation.",
    ]
    for line in lines:
        pdf.drawString(50, y, line)
        y -= 20
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


translations = {
    "العربية": {
        "hero_h1": "احصل على عرض سعر فوري لتثبيت التربة خلال 10 ثواني",
        "hero_sub": "حل اقتصادي لتقليل الغبار وتحسين الطرق الترابية للمزارع، الفلل، المخيمات، والمشاريع.",
        "hero_cta": "احصل على عرضك عبر واتساب",
        "lead": "بيانات العميل",
        "name": "الاسم",
        "phone": "رقم الهاتف",
        "area": "المساحة (م²)",
        "thickness": "السماكة (سم)",
        "results": "التقدير المبدئي",
        "tons": "إجمالي الأطنان التقديرية",
        "cost": "التكلفة التقديرية المبدئية (درهم)",
        "save": "حفظ العميل",
        "saved": "تم حفظ بيانات العميل بنجاح.",
        "invalid": "الرجاء إدخال اسم ورقم هاتف ومساحة صحيحة.",
        "wa": "إرسال التفاصيل عبر واتساب",
        "pdf": "تحميل عرض السعر PDF",
        "note": "السعر النهائي يعتمد على معاينة الموقع وتجهيز الأرض.",
    },
    "English": {
        "hero_h1": "Get an instant soil stabilization quotation in 10 seconds",
        "hero_sub": "A cost-effective solution to reduce dust and improve unpaved roads for farms, villas, camps, and projects.",
        "hero_cta": "Get your quote on WhatsApp",
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
        "results": "Preliminary estimate",
        "tons": "Estimated total tons",
        "cost": "Preliminary estimated cost (AED)",
        "save": "Save lead",
        "saved": "Lead saved successfully.",
        "invalid": "Please enter a valid name, phone, and area.",
        "wa": "Send details on WhatsApp",
        "pdf": "Download PDF quotation",
        "note": "Final price depends on site inspection and ground preparation.",
    },
}

lang = st.selectbox("Language / اللغة", options=["العربية", "English"], index=0)
t = translations[lang]
rtl = lang == "العربية"
db_err = init_db()

st.markdown(f"""<div class='hero {'rtl' if rtl else ''}'>
<h1>{t['hero_h1']}</h1>
<p>{t['hero_sub']}</p>
<span class='pill'>Premium Soil Stabilization</span>
</div>""", unsafe_allow_html=True)

area_m2 = 0.0
thickness_cm = DEFAULT_THICKNESS_CM
name = ""
phone = ""

left, right = st.columns([1.2, 1])
with left:
    st.markdown(f"<div class='premium-card {'rtl' if rtl else ''}'>", unsafe_allow_html=True)
    st.subheader(t["lead"])
    name = st.text_input(t["name"], max_chars=80)
    phone = st.text_input(t["phone"], max_chars=20)
    area_m2 = st.number_input(t["area"], min_value=0.0, value=1000.0, step=10.0)
    thickness_cm = st.select_slider(t["thickness"], options=THICKNESS_OPTIONS, value=DEFAULT_THICKNESS_CM)
    st.markdown("</div>", unsafe_allow_html=True)

coverage = AREA_PER_TON_AT_DEFAULT * (DEFAULT_THICKNESS_CM / thickness_cm)
tons_needed = math.ceil((area_m2 / coverage if coverage > 0 else 0) * 100) / 100
estimated_cost = tons_needed * PRICE_PER_TON_AED

with right:
    st.markdown(f"<div class='premium-card {'rtl' if rtl else ''}'>", unsafe_allow_html=True)
    st.subheader(t["results"])
    st.markdown(f"<div class='metric'><div class='small'>{t['tons']}</div><div class='gold'>{tons_needed:,.2f} ton</div></div>", unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric'><div class='small'>{t['cost']}</div><div class='gold'>AED {estimated_cost:,.2f}</div></div>", unsafe_allow_html=True)
    st.caption(t["note"])
    st.markdown("</div>", unsafe_allow_html=True)

wa_message = (
    "مرحباً، أحتاج تأكيد عرض تثبيت التربة.%0A"
    f"الاسم: {name or 'غير مذكور'}%0A"
    f"الهاتف: {phone or 'غير مذكور'}%0A"
    f"المساحة: {area_m2:,.2f} م²%0A"
    f"السماكة: {thickness_cm} سم%0A"
    f"الأطنان التقديرية: {tons_needed:,.2f}%0A"
    f"التكلفة التقديرية: {estimated_cost:,.2f} درهم%0A"
    "الرجاء التواصل لتحديد زيارة الموقع وتأكيد العرض النهائي."
)
wa_url = f"https://wa.me/{WHATSAPP_NUMBER_E164}?text={quote(wa_message)}"
st.link_button(t["hero_cta"], wa_url, use_container_width=True)

if st.button(t["save"], disabled=bool(db_err)):
    if name.strip() and valid_phone(phone) and area_m2 > 0:
        save_lead(name.strip(), phone.strip(), area_m2, float(thickness_cm), tons_needed, estimated_cost)
        st.success(t["saved"])
    else:
        st.warning(t["invalid"])

st.download_button(
    label=t["pdf"],
    data=make_pdf_quote(lang, name or "N/A", phone or "N/A", area_m2, float(thickness_cm), tons_needed, estimated_cost),
    file_name=f"soil_quote_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
    mime="application/pdf",
    use_container_width=True,
)

st.markdown("<h3 class='section-title rtl'>مناسب لك لأننا نوفر:</h3>", unsafe_allow_html=True)
st.markdown("""
<div class='feature-grid rtl'>
  <div class='feature'>مناسب للمزارع والفلل</div>
  <div class='feature'>تنفيذ سريع</div>
  <div class='feature'>تقدير تكلفة فوري</div>
  <div class='feature'>إرسال مباشر عبر واتساب</div>
  <div class='feature'>عرض PDF جاهز</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<h3 class='section-title rtl'>قبل وبعد تثبيت التربة</h3>", unsafe_allow_html=True)
b1, b2 = st.columns(2)
with b1:
    st.markdown("<div class='placeholder rtl'>قبل: سطح ترابي وغبار مرتفع</div>", unsafe_allow_html=True)
with b2:
    st.markdown("<div class='placeholder rtl'>بعد: سطح أكثر تماسكاً وغبار أقل</div>", unsafe_allow_html=True)
st.markdown("<p class='small-note rtl'>تثبيت التربة يقلل تطاير الغبار ويحسن جودة السطح للاستخدام اليومي والحركة الداخلية.</p>", unsafe_allow_html=True)

st.markdown("<h3 class='section-title rtl'>القطاعات التي نخدمها</h3>", unsafe_allow_html=True)
st.markdown("""
<div class='feature-grid rtl'>
  <div class='feature'>مزارع</div>
  <div class='feature'>فلل واستراحات</div>
  <div class='feature'>مخيمات</div>
  <div class='feature'>طرق داخلية</div>
  <div class='feature'>مواقف مؤقتة</div>
  <div class='feature'>مواقع فعاليات</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='final-cta rtl'>
  <h3>جاهز تعرف تكلفة مشروعك؟</h3>
  <p>احسب الآن وأرسل التفاصيل عبر واتساب</p>
</div>
""", unsafe_allow_html=True)
st.link_button("احسب الآن وأرسل التفاصيل عبر واتساب", wa_url, use_container_width=True)
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
