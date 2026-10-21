"""Cortex EDW: Interactive Enterprise Control Tower.

Streamlit full-stack dashboard demonstrating multi-agent planning, hybrid RAG retrieval,
AST governance inspection, real-time thought streams, and interactive data visualization.
"""

import streamlit as st
import pandas as pd
import time
from cortex.graph import cortex_graph
from cortex.rag.metadata_catalog import ENTERPRISE_TABLES, ENTERPRISE_METRICS
from cortex.governance.telemetry import telemetry

st.set_page_config(
    page_title="Cortex EDW | Enterprise Agentic Data Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1D1D1F; margin-bottom: 0px; }
    .sub-header { font-size: 1.05rem; color: #86868B; margin-bottom: 20px; }
    .metric-card { background-color: #F5F5F7; border-radius: 10px; padding: 15px; border: 1px solid #E5E5EA; }
    .agent-pill { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; margin-right: 5px; }
    .status-badge { padding: 4px 8px; border-radius: 6px; font-size: 0.85rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Sidebar: Domain Switcher & Catalog
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg", width=42)
    st.markdown("### **Cortex EDW Control**")
    st.caption("Apple AiDP Architecture Reference")
    
    st.divider()
    st.markdown("#### 📂 Enterprise Catalog")
    selected_domain = st.selectbox(
        "Filter Domain",
        ["All Domains", "Retail", "AppleCare", "SupplyChain", "Services"]
    )
    
    domain_tables = [t for t in ENTERPRISE_TABLES if selected_domain == "All Domains" or t.domain == selected_domain]
    st.write(f"**Indexed Tables:** {len(domain_tables)}")
    for t in domain_tables:
        with st.expander(f"📊 `{t.table_name}` ({t.domain})"):
            st.caption(t.description)
            cols = [f"`{c.name}` ({c.data_type})" for c in t.columns]
            st.markdown("- " + "\n- ".join(cols[:5]) + ("..." if len(cols) > 5 else ""))

    st.divider()
    st.markdown("#### 🛡️ Governance Guardrails")
    st.markdown("- **Engine**: DuckDB Vectorized OLAP")
    st.markdown("- **Parser**: sqlglot AST Read-Only")
    st.markdown("- **RAG**: BM25 + Dense Cosine (RRF)")
    st.markdown("- **Faithfulness**: Groundedness Scoring")

# Main Interface
st.markdown('<div class="main-header">⚡ Cortex EDW: Enterprise Data-Centric Agent Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Autonomous cognitive pipeline for petabyte-scale warehouse star-schemas across Retail, AppleCare, Supply Chain, and Services</div>', unsafe_allow_html=True)

# Presets
preset_queries = {
    "Retail Revenue & Flagship Store Ranking": "Compare total net sales, units sold, and trade-in units across global flagship stores",
    "Product Line Financial Performance": "Break down revenue, discount amount, and discount percentage by product line",
    "AppleCare Hardware Incident & CSAT Analysis": "What are the most frequent hardware repair subsystems, average turnaround time, and CSAT scores?",
    "Global Supply Chain Logistics & Delay Breakdown": "Analyze component supplier shipments, average transit days, and on-time delivery rates",
    "Services Subscription MRR & Cohort Retention": "Break down active subscriptions and estimated monthly recurring revenue by service tier"
}

st.markdown("##### 💡 Suggested Executive Queries:")
cols_preset = st.columns(len(preset_queries))
selected_query = None

for i, (label, q_text) in enumerate(preset_queries.items()):
    if cols_preset[i].button(label, key=f"btn_{i}"):
        selected_query = q_text

user_input = st.text_input(
    "Enter business question or analytical goal:",
    value=selected_query or "Compare total net sales, units sold, and trade-in units across global flagship stores",
    placeholder="e.g. Which repair channel yields the highest customer satisfaction score?"
)

run_button = st.button("🚀 Execute Autonomous Pipeline", type="primary")

if run_button and user_input:
    with st.spinner("Executing cognitive multi-agent pipeline..."):
        start_time = time.time()
        state = cortex_graph.run(user_input)
        total_time_ms = round((time.time() - start_time) * 1000, 2)

    # Top KPI Metrics Bar
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
    with kpi_col1:
        st.metric("Identified Domain", state.domain)
    with kpi_col2:
        st.metric("Warehouse Rows", len(state.query_result))
    with kpi_col3:
        st.metric("Execution Latency", f"{state.execution_meta.get('execution_time_ms', 0):.1f} ms")
    with kpi_col4:
        ast_label = "✅ Passed" if state.ast_valid else "❌ Blocked"
        st.metric("AST Governance", ast_label)
    with kpi_col5:
        st.metric("Groundedness", f"{state.groundedness_score * 100:.0f}%")

    st.divider()

    # Main Tabs
    tab_brief, tab_viz, tab_sql, tab_agent, tab_rag = st.tabs([
        "📄 Executive Briefing",
        "📈 Interactive Visualization",
        "💻 Governed SQL & Data",
        "🧠 Multi-Agent Thought DAG",
        "🔍 Hybrid RAG Evidence"
    ])

    with tab_brief:
        st.markdown(state.executive_narrative)
        
        anomalies = state.statistical_summary.get("anomalies_detected", [])
        if anomalies:
            st.warning(f"⚠️ **Statistical Anomaly Alert**: {len(anomalies)} data point(s) exceeded the |z| > 2.0 threshold.")

    with tab_viz:
        if not state.query_result.empty and state.chart_spec.get("type") == "bar":
            x_col = state.chart_spec.get("x_axis")
            y_col = state.chart_spec.get("y_axis")
            st.markdown(f"#### {state.chart_spec.get('title')}")
            
            # Render Streamlit Bar Chart
            chart_df = state.query_result.head(10).set_index(x_col)
            st.bar_chart(chart_df[y_col], color="#0071E3")
        else:
            st.info("No numerical chart available for this result structure.")

    with tab_sql:
        col_sql1, col_sql2 = st.columns([1, 1])
        with col_sql1:
            st.markdown("#### Dialect-Correct DuckDB SQL")
            st.code(state.candidate_sql, language="sql")
        with col_sql2:
            st.markdown("#### AST Security Audit")
            st.write(f"- **Read-Only Enforced**: True")
            st.write(f"- **Max Row Limit Injected**: 1,000")
            st.write(f"- **Table Whitelist**: Passed ({state.ast_valid})")
            if state.ast_violations:
                st.error("Violations: " + "; ".join(state.ast_violations))
            else:
                st.success("Query passed all enterprise AST integrity gates.")

        st.markdown("#### Execution Result Preview")
        st.dataframe(state.query_result, use_container_width=True)

    with tab_agent:
        st.markdown("#### Multi-Agent Reasoning Chain & Execution Telemetry")
        for step in state.thought_stream:
            status_color = "🟢" if step["status"] == "SUCCESS" else ("🟡" if step["status"] == "RETRY" else "🔵")
            with st.expander(f"{status_color} **{step['agent']}**: {step['message']}"):
                if step.get("data"):
                    st.json(step["data"])

    with tab_rag:
        st.markdown("#### Hybrid RAG Context Injected into Agent Context")
        ctx = state.retrieved_context
        if ctx:
            st.markdown("##### Linked Tables (Dense + BM25 RRF):")
            for t in ctx.get("tables", []):
                st.markdown(f"- **`{t.table_name}`** (`{t.domain}`): {t.description}")
            
            st.markdown("##### Identified Semantic Metrics:")
            for m in ctx.get("metrics", []):
                st.markdown(f"- **{m.metric_name}**: `{m.formula}`")
                
            st.markdown("##### Retrieved Operational SOPs:")
            for d in ctx.get("documents", []):
                st.info(f"**[{d.doc_id}] {d.title}**\n\n{d.content}")
