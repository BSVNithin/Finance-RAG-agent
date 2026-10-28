import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

# ------------------------------------------------------------
# Northstar Investor Pressure Test — Streamlit demo dashboard
# All company and financial information is synthetic demo data.
# ------------------------------------------------------------
st.set_page_config(
    page_title="Northstar | Investor Pressure Test",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).resolve().parent / "data"

# Clean, presentation-friendly styling using native Streamlit components.
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.6rem; padding-bottom: 2.5rem; max-width: 1440px;}
      .hero {padding: 1.25rem 1.4rem; border: 1px solid rgba(128,128,128,.25);
             border-radius: 16px; margin-bottom: 1rem;}
      .eyebrow {font-size: .78rem; letter-spacing: .12em; text-transform: uppercase;
                opacity: .72; font-weight: 700;}
      .hero h1 {margin: .25rem 0 .3rem 0; font-size: 2rem;}
      .hero p {margin: 0; opacity: .8;}
      div[data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.22);
        padding: 14px 16px; border-radius: 14px; background: rgba(128,128,128,.035);}
      div[data-testid="stMetricLabel"] p {font-size: .88rem;}
      .small-note {font-size: .82rem; opacity: .72;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Leadership rehearsal workspace · FY26 Q2</div>
      <h1>Investor Pressure Test</h1>
      <p>Turn financial signals and disclosed evidence into clear, defensible investor responses.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("Northstar Components Ltd. · Fictional demonstration data only")


def read_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        return pd.read_csv(path)


def get_secret(name: str, default: str = "") -> str:
    """Read Streamlit secret when present, otherwise fall back to environment."""
    try:
        value = st.secrets.get(name, default)
    except (FileNotFoundError, KeyError, RuntimeError):
        value = default
    return os.getenv(name, value) or default


def fmt_cr(value) -> str:
    try:
        return f"₹{float(value):,.0f} Cr"
    except (TypeError, ValueError):
        return "—"


def pct(value, digits=1) -> str:
    try:
        return f"{float(value):.{digits}%}"
    except (TypeError, ValueError):
        return "—"


kpi_df = read_csv("kpi_summary.csv")
pnl = read_csv("quarterly_pnl.csv")
segments = read_csv("segment_performance.csv")
question_bank = read_csv("investor_question_bank.csv")

# Read current and comparison values from KPI CSV, with scenario defaults.
def kpi_value(metric: str, column: str, default):
    if kpi_df.empty or "Metric" not in kpi_df.columns or column not in kpi_df.columns:
        return default
    mask = kpi_df["Metric"].astype(str).str.contains(metric, case=False, na=False, regex=False)
    rows = kpi_df.loc[mask, column]
    if rows.empty or pd.isna(rows.iloc[0]):
        return default
    try:
        return float(rows.iloc[0])
    except (TypeError, ValueError):
        return rows.iloc[0]

revenue = float(kpi_value("Revenue ", "Q2 FY26", 1240))
prior_revenue = float(kpi_value("Revenue ", "Comparison", 1107.14))
margin = float(kpi_value("EBITDA Margin", "Q2 FY26", 0.142))
prior_margin = float(kpi_value("EBITDA Margin", "Comparison", 0.17))
ocf = float(kpi_value("Operating Cash Flow", "Q2 FY26", 68))
prior_ocf = float(kpi_value("Operating Cash Flow", "Comparison", 119.3))
leverage = float(kpi_value("Net Debt / Annualised EBITDA", "Q2 FY26", 2.1))
prior_leverage = float(kpi_value("Net Debt / Annualised EBITDA", "Comparison", 1.5))
revenue_growth = (revenue / prior_revenue - 1) if prior_revenue else 0.12
margin_delta_bps = (margin - prior_margin) * 10000
ocf_change = (ocf / prior_ocf - 1) if prior_ocf else -0.43
ebitda_estimate = revenue * margin

# Sidebar controls and data context.
with st.sidebar:
    st.header("Workspace")
    st.write("**Company:** Northstar Components Ltd.")
    st.write("**Period:** Q2 FY26")
    st.divider()
    st.subheader("Demo data pack")
    st.caption("Figures and transcripts are synthetic and intended for prototype evaluation.")
    st.markdown("**Included datasets**")
    for filename, frame in [
        ("KPI summary", kpi_df),
        ("Quarterly P&L", pnl),
        ("Segment performance", segments),
        ("Investor question bank", question_bank),
    ]:
        st.write(f"{'✓' if not frame.empty else '○'} {filename}")
    st.divider()
    st.caption("Use as a rehearsal aid only. Validate all figures and claims before external use.")

# KPI strip
st.subheader("Executive snapshot")
k1, k2, k3 = st.columns(3)
k1.metric("Revenue", fmt_cr(revenue), f"{revenue_growth:+.1%} YoY")
k2.metric("EBITDA margin", pct(margin), f"{margin_delta_bps:+.0f} bps YoY")
k3.metric("Estimated EBITDA", fmt_cr(ebitda_estimate), "Revenue × reported margin")
k4, k5, k6 = st.columns(3)
k4.metric("Operating cash flow", fmt_cr(ocf), f"{ocf_change:+.1%} YoY")
k5.metric("Net debt / EBITDA", f"{leverage:.1f}×", f"Prior comparison {prior_leverage:.1f}×")
k6.metric("Segment count", f"{segments.loc[segments['Quarter'].eq('Q2 FY26'), 'Segment'].nunique() if not segments.empty and {'Quarter','Segment'}.issubset(segments.columns) else 3}", "Industrial · Mobility · Components")

# High-level alerts based on the scenario.
with st.container(border=True):
    st.markdown("**Investor attention areas**")
    a1, a2, a3 = st.columns(3)
    a1.warning("Margin compression\n\n280 bps decline versus comparison period")
    a2.warning("Cash conversion\n\nOperating cash flow down versus comparison period")
    a3.info("Guidance accountability\n\nReconcile prior recovery language with current results")

# Tabs keep the main experience clean and separate.
tab_overview, tab_agent, tab_questions, tab_trends = st.tabs(
    ["Executive Overview", "Ask the RAG Agent", "Investor Question Bank", "Financial Trends"]
)

with tab_overview:
    left, right = st.columns([1.25, 1])
    with left:
        st.markdown("#### Revenue and profitability")
        if not pnl.empty and "Quarter" in pnl.columns and "Revenue" in pnl.columns:
            chart = pnl.copy()
            chart["Revenue"] = pd.to_numeric(chart["Revenue"], errors="coerce")
            cost_cols = [c for c in ["COGS", "SG&A", "R&D", "Other OpEx"] if c in chart.columns]
            for col in cost_cols:
                chart[col] = pd.to_numeric(chart[col], errors="coerce")
            if cost_cols:
                chart["EBITDA (derived)"] = chart["Revenue"] - chart[cost_cols].sum(axis=1, min_count=1)
                chart["EBITDA Margin (derived)"] = chart["EBITDA (derived)"] / chart["Revenue"]
            st.line_chart(chart.set_index("Quarter")[["Revenue"]], height=260)
            if "EBITDA Margin (derived)" in chart.columns:
                st.line_chart(chart.set_index("Quarter")[["EBITDA Margin (derived)"]], height=220)
                st.caption("EBITDA margin trend is derived from the listed P&L cost lines where available.")
        else:
            st.info("Add quarterly_pnl.csv to streamlit_app/data to show trends.")
    with right:
        st.markdown("#### Segment mix · Q2 FY26")
        if not segments.empty and {"Quarter", "Segment", "Revenue"}.issubset(segments.columns):
            latest = segments[segments["Quarter"].astype(str).eq("Q2 FY26")].copy()
            latest["Revenue"] = pd.to_numeric(latest["Revenue"], errors="coerce")
            if not latest.empty:
                st.bar_chart(latest.set_index("Segment")[["Revenue"]], height=250)
                if "EBITDA Margin" in latest.columns:
                    latest["EBITDA Margin"] = pd.to_numeric(latest["EBITDA Margin"], errors="coerce")
                    st.bar_chart(latest.set_index("Segment")[["EBITDA Margin"]], height=220)
                    st.caption("Segment margins are shown as decimal values (e.g., 0.168 = 16.8%).")
        st.markdown("#### Leadership focus")
        st.markdown(
            "- Quantify the 280 bps margin decline.\n"
            "- Reconcile operating cash flow with working-capital movements.\n"
            "- Compare prior margin-recovery guidance with actual delivery."
        )

with tab_agent:
    st.subheader("Prepare an evidence-backed answer")
    st.caption("Ask a difficult investor question. The agent retrieves sources and drafts a response for human review.")
    question = st.text_area(
        "Investor question",
        value="Revenue grew 12%, so why did EBITDA margin fall 280 bps versus the prior-year comparison?",
        height=100,
        placeholder="Enter a question from an investor or analyst...",
        label_visibility="visible",
    )
    quarter_options = ["All quarters", "Q1 FY25", "Q2 FY25", "Q3 FY25", "Q4 FY25", "Q1 FY26", "Q2 FY26"]
    selected_quarter = st.selectbox("Evidence period", quarter_options, index=0)
    webhook = get_secret("N8N_WEBHOOK_URL", "")
    if st.button("Generate investor response", type="primary", use_container_width=False):
        if not webhook:
            st.error("Configure N8N_WEBHOOK_URL in streamlit_app/.streamlit/secrets.toml.")
        elif not question.strip():
            st.warning("Please enter an investor question.")
        else:
            payload = {
                "question": question.strip(),
                "quarter": None if selected_quarter == "All quarters" else selected_quarter,
                "top_k": 5,
            }
            try:
                with st.spinner("Reviewing the source pack and preparing a draft..."):
                    response = requests.post(webhook, json=payload, timeout=90)
                    response.raise_for_status()
                    data = response.json()
                st.divider()
                st.markdown("#### Suggested leadership response")
                answer = data.get("answer_scaffold") or data.get("answer") or "No answer was returned."
                st.markdown(answer)
                risk = str(data.get("risk_level", "Not assessed")).strip().title()
                if risk.lower() in {"critical", "high"}:
                    st.warning(f"Risk level: {risk} · Review before use")
                elif risk.lower() == "medium":
                    st.info(f"Risk level: {risk}")
                else:
                    st.caption(f"Risk level: {risk}")
                guidance_gap = data.get("guidance_gap")
                if guidance_gap:
                    with st.expander("Guidance and performance gap"):
                        st.write(guidance_gap)
                missing = data.get("missing_evidence", [])
                if isinstance(missing, str):
                    missing = [missing]
                if missing:
                    with st.expander("What leadership still needs to verify"):
                        for item in missing:
                            st.markdown(f"- {item}")
                evidence = data.get("evidence", []) or data.get("citations", []) or []
                if evidence:
                    with st.expander(f"View supporting sources ({len(evidence)})"):
                        for i, item in enumerate(evidence, start=1):
                            if isinstance(item, dict):
                                label = item.get("citation") or item.get("source_file") or item.get("document_id") or f"Source {i}"
                                similarity = item.get("similarity")
                                if similarity is not None:
                                    try:
                                        label = f"{label} · relevance {float(similarity):.2f}"
                                    except (TypeError, ValueError):
                                        pass
                                # Avoid nested expanders: Streamlit does not support it.
                                st.markdown(f"**{i}. {label}**")
                                source_text = item.get("text") or item.get("content") or item.get("snippet")
                                if source_text:
                                    st.caption(str(source_text))
                                else:
                                    st.caption("Source metadata returned; text unavailable.")
                                if i < len(evidence):
                                    st.divider()
                            else:
                                st.write(f"{i}. {item}")
                st.caption("AI-generated rehearsal draft. Validate figures, citations, and forward-looking statements before use.")
            except requests.RequestException as exc:
                st.error(f"Could not reach the n8n workflow. Check the Production URL and workflow status. Details: {exc}")
            except (ValueError, TypeError) as exc:
                st.error(f"The workflow returned an unexpected response format: {exc}")

with tab_questions:
    st.subheader("Investor question bank")
    st.caption("Prioritize questions that need validated data or CFO/FP&A review.")
    if not question_bank.empty:
        display = question_bank.copy()
        if "Priority" in display.columns:
            priority_filter = st.multiselect(
                "Filter by priority",
                options=[x for x in ["Critical", "High", "Medium", "Low"] if x in display["Priority"].astype(str).unique()],
                default=[x for x in ["Critical", "High", "Medium", "Low"] if x in display["Priority"].astype(str).unique()],
            )
            display = display[display["Priority"].astype(str).isin(priority_filter)]
        preferred = [c for c in ["Priority", "Investor question", "Trigger / metric", "Evidence required", "Escalation / evidence gap"] if c in display.columns]
        if preferred:
            st.dataframe(display[preferred], use_container_width=True, hide_index=True)
        else:
            st.dataframe(display, use_container_width=True, hide_index=True)
    else:
        st.info("Place investor_question_bank.csv in streamlit_app/data to display the question bank.")

with tab_trends:
    st.subheader("Financial performance trends")
    if pnl.empty:
        st.info("Place quarterly_pnl.csv in streamlit_app/data to show quarterly financial trends.")
    else:
        chart = pnl.copy()
        for col in chart.columns:
            if col not in {"Quarter", "Period End"}:
                chart[col] = pd.to_numeric(chart[col], errors="coerce")
        # Derive gross profit, EBITDA and margins from the available cost lines when not populated.
        if {"Revenue", "COGS"}.issubset(chart.columns):
            chart["Gross Profit (derived)"] = chart["Revenue"] - chart["COGS"]
            chart["Gross Margin (derived)"] = chart["Gross Profit (derived)"] / chart["Revenue"]
        expense_cols = [c for c in ["COGS", "SG&A", "R&D", "Other OpEx"] if c in chart.columns]
        if expense_cols and "Revenue" in chart.columns:
            chart["EBITDA (derived)"] = chart["Revenue"] - chart[expense_cols].sum(axis=1, min_count=1)
            chart["EBITDA Margin (derived)"] = chart["EBITDA (derived)"] / chart["Revenue"]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Revenue by quarter (₹ Cr)")
            st.bar_chart(chart.set_index("Quarter")[["Revenue"]], use_container_width=True)
        with col2:
            st.markdown("#### Cost and profit profile (₹ Cr)")
            show_cols = [c for c in ["COGS", "SG&A", "R&D", "Other OpEx", "EBITDA (derived)"] if c in chart.columns]
            if show_cols:
                st.line_chart(chart.set_index("Quarter")[show_cols], use_container_width=True)
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("#### Gross margin trend")
            if "Gross Margin (derived)" in chart.columns:
                st.line_chart(chart.set_index("Quarter")[["Gross Margin (derived)"]], use_container_width=True)
        with col4:
            st.markdown("#### EBITDA margin trend")
            if "EBITDA Margin (derived)" in chart.columns:
                st.line_chart(chart.set_index("Quarter")[["EBITDA Margin (derived)"]], use_container_width=True)
        st.caption("Derived measures are calculated from the synthetic P&L cost lines; they are not audited company results.")

    if not segments.empty and {"Quarter", "Segment", "Revenue"}.issubset(segments.columns):
        st.divider()
        st.subheader("Segment performance")
        seg = segments.copy()
        seg["Revenue"] = pd.to_numeric(seg["Revenue"], errors="coerce")
        if "EBITDA Margin" in seg.columns:
            seg["EBITDA Margin"] = pd.to_numeric(seg["EBITDA Margin"], errors="coerce")
        selected = st.selectbox("Select quarter for segment comparison", sorted(seg["Quarter"].dropna().unique()), index=len(sorted(seg["Quarter"].dropna().unique())) - 1)
        current = seg[seg["Quarter"].eq(selected)].copy()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### Segment revenue · {selected} (₹ Cr)")
            st.bar_chart(current.set_index("Segment")[["Revenue"]], use_container_width=True)
        with c2:
            st.markdown(f"#### Segment EBITDA margin · {selected}")
            if "EBITDA Margin" in current.columns:
                st.bar_chart(current.set_index("Segment")[["EBITDA Margin"]], use_container_width=True)
        show_cols = [c for c in ["Segment", "Revenue", "YoY Growth", "EBITDA Margin", "Management / interpretation note"] if c in current.columns]
        st.dataframe(current[show_cols], use_container_width=True, hide_index=True)

st.divider()
st.caption("Prototype only · All Northstar figures and transcripts are synthetic · Finance/Legal review required before external use")
