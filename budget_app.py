import streamlit as st

st.set_page_config(page_title="💰 حاسبة الميزانية الشهرية")

st.title("💰 حاسبة الميزانية الشهرية")
st.caption("أدخل دخلك ومصاريفك وشوف الرصيد الشهري مباشرة 👇")

income = st.number_input("الدخل الشهري (درهم)", min_value=0.0, step=100.0)
expenses = st.number_input("المصاريف الشهرية (درهم)", min_value=0.0, step=100.0)

balance = income - expenses

if balance >= 0:
    st.success(f"رصيدك الشهري: {balance:.2f} درهم ✅")
else:
    st.error(f"رصيدك الشهري بالسالب: {balance:.2f} درهم ⚠️")

st.progress(min(1.0, expenses / income) if income > 0 else 0.0)
