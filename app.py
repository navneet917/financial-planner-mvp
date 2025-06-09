import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

st.set_page_config(page_title="Client Financial Planner", layout="wide")
st.title("📊 Personal Financial Planning MVP")

st.sidebar.header("Upload Client Excel or Enter Manually")
uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])
st.sidebar.markdown("---")
manual_mode = st.sidebar.checkbox("Enter Data Manually")

client_data = {}

def calculate_recommendations(data):
    recs = []
    if data['savings_rate'] < 0.25:
        recs.append("Increase savings rate to at least 25% by reducing expenses.")
    if data['ret_corpus_gap'] > 1000000:
        recs.append(f"To close retirement gap of Rs {data['ret_corpus_gap']:,}, start SIP of Rs {int(data['sip_needed']):,}/mo.")
    if data['goal_funded'] < 0.5:
        recs.append("Increase allocation to priority goals to reach 50% funded.")
    return recs or ["You are on track with current goals and savings!"]

if manual_mode:
    st.subheader("Manual Input Mode")
    client_data['name'] = st.text_input("Client Name", "John Doe")
    client_data['age'] = st.number_input("Age", 30, 60, 40)
    client_data['income'] = st.number_input("Annual Income (Rs)", 0, 100000000, 1200000, step=10000)
    client_data['expenses'] = st.number_input("Annual Expenses (Rs)", 0, 100000000, 800000, step=10000)
    client_data['debt'] = st.number_input("Total Debt (Rs)", 0, 100000000, 200000)
    client_data['goal_amount'] = st.number_input("Goal: Child Education (Rs)", 0, 100000000, 1500000)
    client_data['goal_current'] = st.number_input("Current Saved for Goal (Rs)", 0, 100000000, 500000)

    client_data['savings_rate'] = 1 - client_data['expenses'] / client_data['income']
    years_to_ret = 65 - client_data['age']
    expenses_at_ret = client_data['expenses'] * ((1 + 0.08) ** years_to_ret)
    pv_factor = (1 - 1 / ((1 + 0.06) ** 25)) / 0.06
    corpus_required = expenses_at_ret * pv_factor
    fv_savings = (client_data['income'] * client_data['savings_rate']) * ((1 + 0.12) ** years_to_ret)
    corpus_gap = max(0, corpus_required - fv_savings)
    sip_factor = (((1 + 0.12/12)**(years_to_ret*12)) - 1) / (0.12/12)
    sip_needed = corpus_gap / sip_factor if corpus_gap > 0 else 0
    goal_funded = client_data['goal_current'] / client_data['goal_amount']

    client_data.update({
        'ret_corpus_required': corpus_required,
        'ret_corpus_gap': corpus_gap,
        'sip_needed': sip_needed,
        'goal_funded': goal_funded
    })

    st.markdown("---")
    st.subheader("Summary")
    st.json(client_data)

    st.subheader("📌 Recommendations")
    for r in calculate_recommendations(client_data):
        st.success(r)

    buffer = io.BytesIO()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Financial Report: {client_data['name']}", ln=True)
    pdf.cell(0, 10, f"Age: {client_data['age']} | Income: Rs {client_data['income']:,} | Expenses: Rs {client_data['expenses']:,}", ln=True)
    pdf.cell(0, 10, f"Savings Rate: {client_data['savings_rate']*100:.1f}% | Debt: Rs {client_data['debt']:,}", ln=True)
    pdf.cell(0, 10, f"Retirement Corpus Needed: Rs {int(corpus_required):,}", ln=True)
    pdf.cell(0, 10, f"Corpus Gap: Rs {int(corpus_gap):,} | SIP Needed: Rs {int(sip_needed):,}/mo", ln=True)
    pdf.cell(0, 10, f"Goal Funded: {goal_funded*100:.1f}%", ln=True)
    pdf.ln(10)
    pdf.cell(0, 10, "Recommendations:", ln=True)
    for r in calculate_recommendations(client_data):
        pdf.cell(0, 10, f"- {r}", ln=True)
    pdf.output(buffer)
    st.download_button("📥 Download PDF Report", data=buffer.getvalue(), file_name="Financial_Report.pdf", mime="application/pdf")
