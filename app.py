"""
PayWeave — Declarative Payment Application & Intelligent Infrastructure Framework.
Main Streamlit Application Entrypoint.
Features ultra-stunning glassmorphic dark fintech aesthetic, live Plotly visualizations,
low-code visual flow graph builder, self-healing timeline, and AI operations.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time
import os

from payweave.dsl.schema import MerchantConfig, RoutingStrategy, AuthMode, UILayout, UITheme
from payweave.dsl.parser import DSLParser
from payweave.dsl.validator import DSLValidator
from payweave.runtime.engine import PayWeaveEngine
from payweave.runtime.functional_core import PaymentRequest
from payweave.anomaly.detector import AnomalyDetector
from payweave.anomaly.simulator import TelemetrySimulator
from payweave.aiops.payment_assist import PayWeaveAssist
from payweave.aiops.incident_analyzer import IncidentAnalyzer
from payweave.aiops.llm_client import LLMClient
from payweave.infrastructure.infrastructure_dsl import InfrastructureDSLParser
from payweave.infrastructure.topology import TopologyVisualizer
from payweave.infrastructure.multi_dc import MultiDCSimulator
from payweave.infrastructure.edge import EdgeComputingSimulator
from payweave.analytics.metrics import MetricsCollector
from payweave.analytics.aggregations import AnalyticsAggregator

# Page Configuration
st.set_page_config(
    page_title="PayWeave — Declarative Payment Framework",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Advanced Glassmorphic Dark Aesthetics CSS
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Theme Overrides */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: #0B0F17;
        background-image: 
            radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(56, 189, 248, 0.12) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(168, 85, 247, 0.1) 0px, transparent 50%);
        background-attachment: fixed;
        color: #F8FAFC;
    }
    
    /* Premium Header Banner */
    .main-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 28px 36px;
        margin-bottom: 24px;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #818CF8 0%, #C084FC 40%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        font-weight: 500;
        margin-top: 6px;
    }

    /* Status Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(52, 211, 153, 0.3);
    }
    
    /* Glowing Stat Cards */
    .stat-card-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }

    .stat-card {
        background: rgba(30, 41, 59, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(12px);
        transition: transform 0.2s ease, border-color 0.2s ease;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }
    .stat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
    }
    .stat-card.indigo::before { background: linear-gradient(90deg, #6366F1, #818CF8); }
    .stat-card.cyan::before { background: linear-gradient(90deg, #06B6D4, #38BDF8); }
    .stat-card.emerald::before { background: linear-gradient(90deg, #059669, #34D399); }
    .stat-card.amber::before { background: linear-gradient(90deg, #D97706, #FBBF24); }
    .stat-card.rose::before { background: linear-gradient(90deg, #E11D48, #FB7185); }

    .stat-label {
        color: #94A3B8;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .stat-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-top: 6px;
        letter-spacing: -0.02em;
    }
    .stat-desc {
        font-size: 0.78rem;
        color: #64748B;
        margin-top: 4px;
    }

    /* Disclaimer alert */
    .disclaimer-banner {
        background: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.25);
        padding: 12px 20px;
        border-radius: 12px;
        font-size: 0.88rem;
        color: #FCD34D;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Code & Log Blocks */
    .stCodeBlock {
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Custom Streamlit Radio Buttons in Sidebar */
    div[data-testid="stSidebarNav"] {
        background-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State Engine & Services
if "engine" not in st.session_state:
    st.session_state.engine = PayWeaveEngine()

if "multi_dc" not in st.session_state:
    st.session_state.multi_dc = MultiDCSimulator()

if "edge_sim" not in st.session_state:
    st.session_state.edge_sim = EdgeComputingSimulator()

if "telemetry" not in st.session_state:
    st.session_state.telemetry = TelemetrySimulator.generate_telemetry_stream(num_records=50)

if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("GEMINI_API_KEY", "")

engine = st.session_state.engine
multi_dc = st.session_state.multi_dc
edge_sim = st.session_state.edge_sim

# Sidebar Configuration
st.sidebar.markdown("### ⚡ PAYWEAVE PLATFORM")
st.sidebar.caption("Declarative Payment & Intelligent Infrastructure")

page = st.sidebar.radio(
    "Framework Navigation",
    [
        "🏠 Home & Overview",
        "🎛️ Merchant Console",
        "🧩 Flow Builder (Low-Code)",
        "💳 Payment Simulator",
        "🧠 Intelligent Router",
        "🛡️ Self-Healing System",
        "📈 Anomaly Detection",
        "🤖 AI Payment Operations",
        "🌐 Infrastructure & Multi-DC",
        "🧪 Reliability Lab",
        "📚 API & Functional Core"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 AI Operations Config")
user_key_input = st.sidebar.text_input(
    "Gemini / Groq API Key",
    value=st.session_state.api_key,
    type="password",
    help="Optional: Enter your Gemini key (e.g. AQ... or AIza...). Works 100% offline if blank!"
)
if user_key_input != st.session_state.api_key:
    st.session_state.api_key = user_key_input
    if user_key_input:
        os.environ["GEMINI_API_KEY"] = user_key_input
        st.sidebar.success("API Key activated!")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 Runtime Controls")
if st.sidebar.button("🔄 Reset Simulation State", use_container_width=True):
    engine.reset_simulation()
    multi_dc.recover_dc("dc1")
    multi_dc.recover_dc("dc2")
    st.session_state.telemetry = TelemetrySimulator.generate_telemetry_stream(num_records=50)
    st.sidebar.success("Simulation metrics reset!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='font-size: 11px; color: #64748B; text-align: center;'>"
    "PayWeave Portfolio Simulation v1.0<br>"
    "Synthetic Workload Engine"
    "</div>",
    unsafe_allow_html=True
)

# Header Banner
st.markdown("""
<div class="main-header">
    <div>
        <div class="main-title">PAYWEAVE</div>
        <div class="subtitle">Declarative Payment Application & Intelligent Infrastructure Framework</div>
    </div>
    <div>
        <div class="status-badge">🟢 OPERATIONAL SLA: 99.9%</div>
    </div>
</div>
<div class="disclaimer-banner">
    ⚠️ <b>Portfolio Simulation Notice:</b> PayWeave is an architectural demonstration framework.
    All transactions, provider metrics, and telemetry are synthetic simulations. No real money or bank credentials are used.
</div>
""", unsafe_allow_html=True)


# Helper function for Plotly Dark Neon Theme
def apply_plotly_theme(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans", color="#F8FAFC"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)"),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(bgcolor="rgba(30,41,59,0.5)")
    )
    return fig


# Page 1: Home & Overview
if page == "🏠 Home & Overview":
    health_map = engine.get_provider_health_map()
    succ_rates = [h.success_rate for h in health_map.values()]
    avg_succ = (sum(succ_rates) / len(succ_rates)) * 100 if succ_rates else 99.1
    active_providers = sum(1 for h in health_map.values() if h.is_healthy)
    healing_events = len(engine.self_healing.events)
    
    detector = AnomalyDetector()
    anomalies = detector.detect_batch_anomalies(st.session_state.telemetry)
    anomaly_count = sum(1 for a in anomalies if a.anomaly_detected)

    st.markdown(f"""
    <div class="stat-card-container">
        <div class="stat-card emerald">
            <div class="stat-label">System Health</div>
            <div class="stat-value" style="color: #34D399">{avg_succ:.1f}%</div>
            <div class="stat-desc">Rolling SLA Compliance</div>
        </div>
        <div class="stat-card cyan">
            <div class="stat-label">Active Providers</div>
            <div class="stat-value" style="color: #38BDF8">{active_providers} / 3</div>
            <div class="stat-desc">PSP-A, PSP-B, PSP-C</div>
        </div>
        <div class="stat-card indigo">
            <div class="stat-label">Routing Strategy</div>
            <div class="stat-value" style="color: #818CF8; font-size: 1.4rem;">{engine.config.routing.strategy.upper()}</div>
            <div class="stat-desc">Multi-Factor Scoring</div>
        </div>
        <div class="stat-card amber">
            <div class="stat-label">Anomalies Detected</div>
            <div class="stat-value" style="color: #FBBF24">{anomaly_count}</div>
            <div class="stat-desc">Z-Score Threshold Exceeded</div>
        </div>
        <div class="stat-card rose">
            <div class="stat-label">Self-Healing Events</div>
            <div class="stat-value" style="color: #FB7185">{healing_events}</div>
            <div class="stat-desc">Circuit Breakers Triggered</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Real-time Synthetic Transaction Volume & Throughput")
        df_telem = pd.DataFrame(st.session_state.telemetry)
        
        fig_vol = px.line(
            df_telem,
            x="formatted_time",
            y="transaction_count",
            color="provider",
            title="Transaction Throughput by Provider (tx/min)",
            color_discrete_sequence=["#818CF8", "#38BDF8", "#FBBF24"]
        )
        st.plotly_chart(apply_plotly_theme(fig_vol), use_container_width=True)

    with col2:
        st.markdown("#### Provider Health Matrix")
        df_comp = AnalyticsAggregator.build_provider_comparison_df(health_map)
        st.dataframe(df_comp, hide_index=True, use_container_width=True)

        st.markdown("#### Dynamic Operational Summary")
        analyzer = IncidentAnalyzer()
        summary_text = analyzer.generate_operational_summary(health_map, engine.self_healing.get_timeline(), anomaly_count)
        st.info(summary_text)


# Page 2: Merchant Console
elif page == "🎛️ Merchant Console":
    st.markdown("### Merchant Self-Service Console")
    st.caption("Declarative customization portal for payment methods, risk policies, step-up authentication, and UI styling.")

    tabs = st.tabs(["📋 General & Methods", "🔀 Routing Policies", "🛡️ Risk & Auth Rules", "🎨 UI Customization", "📄 Export YAML DSL", "📜 Audit Log"])

    with tabs[0]:
        st.markdown("#### Merchant Parameters")
        m_name = st.text_input("Merchant Display Name", engine.config.merchant.name)
        m_id = st.text_input("Merchant ID", engine.config.merchant.id)
        selected_methods = st.multiselect("Supported Payment Methods", ["upi", "card", "netbanking"], engine.config.payment.methods)
        
        if st.button("Save General Settings"):
            engine.config.merchant.name = m_name
            engine.config.merchant.id = m_id
            engine.config.payment.methods = selected_methods
            engine.reload_config(engine.config)
            st.success("Merchant config updated successfully!")

    with tabs[1]:
        st.markdown("#### Intelligent Routing & Fallbacks")
        strat = st.selectbox(
            "Routing Strategy Algorithm",
            ["intelligent", "highest_success_rate", "lowest_latency", "lowest_cost", "balanced"],
            index=0
        )
        fallback_enabled = st.checkbox("Enable Automated Fallback", engine.config.routing.fallback.enabled)
        max_retries = st.slider("Max Retries Before Circuit Break", 0, 5, engine.config.routing.fallback.max_retries)

        if st.button("Save Routing Policies"):
            engine.config.routing.strategy = RoutingStrategy(strat)
            engine.config.routing.fallback.enabled = fallback_enabled
            engine.config.routing.fallback.max_retries = max_retries
            engine.reload_config(engine.config)
            st.success("Routing strategy saved!")

    with tabs[2]:
        st.markdown("#### Fraud Risk Caps & Adaptive Security")
        r_max = st.slider("Max Allowed Risk Score (0.0 - 1.0)", 0.1, 1.0, float(engine.config.risk.max_score), 0.05)
        block_high = st.checkbox("Automatically Block High Risk Transactions", engine.config.risk.block_high_risk)
        
        auth_mode = st.selectbox("Authentication Security Mode", ["adaptive", "frictionless", "always_2fa"], index=0)
        step_up_th = st.slider("Adaptive Step-up 2FA Risk Threshold", 0.1, 1.0, float(engine.config.authentication.step_up_threshold), 0.05)

        if st.button("Save Risk Policies"):
            engine.config.risk.max_score = r_max
            engine.config.risk.block_high_risk = block_high
            engine.config.authentication.mode = AuthMode(auth_mode)
            engine.config.authentication.step_up_threshold = step_up_th
            engine.reload_config(engine.config)
            st.success("Security policies saved!")

    with tabs[3]:
        st.markdown("#### Declarative Checkout Page Styling")
        brand = st.text_input("Brand Display Name", engine.config.payment_page.brand_name)
        color = st.color_picker("Brand Accent Color", engine.config.payment_page.primary_color)

        if st.button("Apply UI Configuration"):
            engine.config.payment_page.brand_name = brand
            engine.config.payment_page.primary_color = color
            engine.reload_config(engine.config)
            st.success("Checkout UI theme updated!")

    with tabs[4]:
        st.markdown("#### Generated Declarative YAML DSL")
        yaml_out = DSLParser.to_yaml(engine.config)
        st.code(yaml_out, language="yaml")

    with tabs[5]:
        st.markdown("#### Configuration Change Audit Log")
        audit_logs = engine.db.get_audit_logs()
        if audit_logs:
            st.dataframe(pd.DataFrame(audit_logs), use_container_width=True)
        else:
            st.info("No audit logs recorded yet.")


# Page 3: Flow Builder
elif page == "🧩 Flow Builder (Low-Code)":
    st.markdown("### Visual Low-Code Payment Flow Builder")
    st.caption("Construct payment execution pipelines visually. Changes automatically update the Declarative YAML DSL.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Visual Node Configuration")
        risk_node = st.slider("Risk Check Node: Max Risk Score", 0.1, 1.0, float(engine.config.risk.max_score), 0.05)
        auth_node = st.selectbox("Auth Node: Security Mode", ["adaptive", "frictionless", "always_2fa"])
        route_node = st.selectbox("Route Node: Strategy", ["intelligent", "highest_success_rate", "lowest_latency", "lowest_cost"])
        retry_node = st.number_input("Fallback Node: Max Retries", 0, 5, engine.config.routing.fallback.max_retries)

        if st.button("⚡ Update Flow Graph & Recompile DSL"):
            engine.config.risk.max_score = risk_node
            engine.config.authentication.mode = AuthMode(auth_node)
            engine.config.routing.strategy = RoutingStrategy(route_node)
            engine.config.routing.fallback.max_retries = retry_node
            engine.reload_config(engine.config)
            st.success("Flow pipeline compiled successfully!")

    with col2:
        st.markdown("#### Generated Visual Graph Diagram")
        flow_nodes = DSLParser.config_to_flow_nodes(engine.config)
        mermaid_lines = ["graph TD"]
        for i in range(len(flow_nodes) - 1):
            curr = flow_nodes[i]
            nxt = flow_nodes[i+1]
            mermaid_lines.append(f"    {curr['id']}[\"<b>{curr['label']}</b><br><small>{curr['description']}</small>\"] --> {nxt['id']}[\"<b>{nxt['label']}</b><br><small>{nxt['description']}</small>\"]")
        
        st.markdown(f"```mermaid\n{chr(10).join(mermaid_lines)}\n```")


# Page 4: Payment Simulator
elif page == "💳 Payment Simulator":
    st.markdown("### Interactive Payment Simulator")
    st.caption("Execute simulated transactions to observe step-by-step risk scoring, adaptive 2FA, intelligent provider routing, and automatic fallback.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Transaction Input")
        sim_amt = st.number_input("Transaction Amount (₹)", min_value=1.0, value=2500.0, step=100.0)
        sim_method = st.selectbox("Payment Method", engine.config.payment.methods)
        sim_curr = st.selectbox("Currency", engine.config.payment.currencies)
        sim_risk = st.slider("Simulated Risk Score", 0.0, 1.0, 0.10, 0.05)
        
        force_fail = st.selectbox(
            "Inject Synthetic Failure (Testing)",
            ["None", "psp-a", "psp-b", "psp-c"],
            help="Forces a provider to fail to test automatic fallback rerouting."
        )
        fail_provider = None if force_fail == "None" else force_fail

        if st.button("🚀 Process Simulated Payment", use_container_width=True):
            with st.spinner("Processing execution plan..."):
                outcome = engine.process_payment(
                    amount=sim_amt,
                    payment_method=sim_method,
                    currency=sim_curr,
                    risk_score=sim_risk,
                    simulate_failure_provider=fail_provider
                )
                st.session_state.last_outcome = outcome

    with col2:
        st.markdown("#### Runtime Execution Result")
        if "last_outcome" in st.session_state:
            out = st.session_state.last_outcome
            if out.success:
                st.success(f"✅ {out.message}")
            else:
                st.error(f"❌ {out.message}")

            st.json({
                "transaction_id": out.transaction_id,
                "provider_used": out.provider_used.upper(),
                "attempted_providers": out.attempted_providers,
                "retries_count": out.retries_count,
                "total_latency_ms": f"{out.total_latency_ms} ms",
                "status_code": out.status_code
            })


# Page 5: Intelligent Router
elif page == "🧠 Intelligent Router":
    st.markdown("### Intelligent Payment Router")
    st.caption("Multi-dimensional dynamic scoring engine ranking candidate PSP adapters.")

    health_map = engine.get_provider_health_map()
    
    st.markdown("#### Provider Health & Scoring Matrix")
    df_comp = AnalyticsAggregator.build_provider_comparison_df(health_map)
    st.dataframe(df_comp, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Multi-Dimensional Provider Radar Comparison")

    fig_radar = go.Figure()
    for pid, h in health_map.items():
        fig_radar.add_trace(go.Scatterpolar(
            r=[h.success_rate * 100, max(0, 100 - h.latency_ms / 5), (1.0 - h.cost_score) * 100, h.capacity_pct],
            theta=["Success Rate", "Low Latency Score", "Cost Efficiency", "Capacity"],
            fill='toself',
            name=pid.upper()
        ))

    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans", color="#F8FAFC")
    )
    st.plotly_chart(fig_radar, use_container_width=True)


# Page 6: Self-Healing System
elif page == "🛡️ Self-Healing System":
    st.markdown("### Self-Healing System & Recovery Timeline")
    st.caption("Monitors provider health, reduces scores on degradation, shifts traffic, and records timeline audit events.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Failure Injection Lab")
        target_psp = st.selectbox("Select Provider to Degrade", ["psp-a", "psp-b", "psp-c"])
        lat_mult = st.slider("Latency Spike Multiplier", 2.0, 5.0, 3.5, 0.5)
        succ_drop = st.slider("Success Rate Drop", 0.1, 0.6, 0.35, 0.05)

        if st.button("🔥 Simulate Degradation Event"):
            events = engine.self_healing.trigger_manual_failure(target_psp, lat_mult, succ_drop)
            st.warning(f"Degradation injected into {target_psp.upper()}. {len(events)} self-healing events recorded.")

        if st.button("🟢 Restore Provider Baseline Health"):
            events = engine.self_healing.trigger_manual_recovery(target_psp)
            st.success(f"Health restored for {target_psp.upper()}.")

    with col2:
        st.markdown("#### Recovery Timeline Logs")
        timeline = engine.self_healing.get_timeline()
        if timeline:
            for ev in timeline:
                sev_color = "#EF4444" if ev["severity"] == "CRITICAL" else "#F59E0B" if ev["severity"] == "WARNING" else "#10B981"
                st.markdown(
                    f"<div style='border-left: 3px solid {sev_color}; padding-left: 10px; margin-bottom: 12px; background: rgba(30,41,59,0.5); padding: 8px 12px; border-radius: 6px;'>"
                    f"<b>[{ev['time']}] {ev['event_type']} ({ev['provider_id'].upper()})</b><br>"
                    f"<small>{ev['description']}</small><br>"
                    f"<span style='color: #38BDF8;'>Action: {ev['action_taken']}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No self-healing events recorded yet. Trigger a degradation event to test automated rerouting.")


# Page 7: Anomaly Detection
elif page == "📈 Anomaly Detection":
    st.markdown("### Telemetry Anomaly Detector")
    st.caption("Rolling statistical Z-score detector flagging latency spikes, success rate drops, and error bursts.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### Anomaly Controls")
        inject_psp = st.selectbox("Inject Synthetic Anomaly", ["None", "psp-a", "psp-b", "psp-c"])
        inj_target = None if inject_psp == "None" else inject_psp
        sensitivity = st.slider("Anomaly Sensitivity Cutoff", 0.3, 0.9, 0.65, 0.05)

        if st.button("⚡ Regenerate Telemetry Stream"):
            st.session_state.telemetry = TelemetrySimulator.generate_telemetry_stream(
                num_records=50, inject_anomaly_provider=inj_target
            )
            st.success("Telemetry regenerated!")

    with col2:
        detector = AnomalyDetector()
        reports = detector.detect_batch_anomalies(st.session_state.telemetry, sensitivity_threshold=sensitivity)

        st.markdown("#### Anomaly Diagnostic Reports")
        for r in reports:
            if r.anomaly_detected:
                st.error(f"🚨 **{r.severity} ANOMALY ({r.affected_provider.upper()})** - Score: {r.anomaly_score:.2f}\n\n{r.explanation}")
            else:
                st.success(f"🟢 **NORMAL ({r.affected_provider.upper()})** - Score: {r.anomaly_score:.2f}\n\n{r.explanation}")

    st.markdown("---")
    st.markdown("#### Live Telemetry Stream Charts")
    df_t = pd.DataFrame(st.session_state.telemetry)
    fig_lat = px.line(df_t, x="formatted_time", y="latency", color="provider", title="Telemetry Latency Stream (ms)")
    st.plotly_chart(apply_plotly_theme(fig_lat), use_container_width=True)


# Page 8: AI Payment Operations
elif page == "🤖 AI Payment Operations":
    st.markdown("### PayWeave Assist — AI Operations Assistant")
    st.caption("Ask natural language questions about payment performance, outages, routing reasons, and cost minimization.")

    llm_client = LLMClient(override_gemini_key=st.session_state.api_key)
    assist = PayWeaveAssist(llm_client=llm_client)

    if llm_client.has_api_key:
        st.markdown("<div style='color: #34D399; font-weight: 600; margin-bottom: 12px;'>🔑 Active LLM API Key Detected (Live AI Mode)</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color: #FBBF24; font-weight: 600; margin-bottom: 12px;'>⚡ Offline Mode Active (PayWeave Deterministic Response Engine)</div>", unsafe_allow_html=True)

    health_map = engine.get_provider_health_map()
    recent_events = engine.self_healing.get_timeline()

    sample_queries = [
        "Why did PSP-A lose traffic?",
        "Which provider is currently healthiest?",
        "What caused the latency spike?",
        "What would happen if DC-1 failed?",
        "Which routing strategy minimizes cost?"
    ]
    
    selected_query = st.selectbox("Sample Questions", sample_queries)
    custom_query = st.text_input("Or ask a custom question:", selected_query)

    if st.button("🤖 Generate AI Operational Analysis"):
        with st.spinner("Analyzing operational telemetry and generating response..."):
            ans = assist.ask(custom_query, engine.config, health_map, recent_events)
            st.markdown("---")
            st.markdown(
                f"<div style='background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.12); font-size: 1rem; color: #F8FAFC;'>"
                f"{ans}"
                f"</div>",
                unsafe_allow_html=True
            )


# Page 9: Infrastructure & Multi-DC
elif page == "🌐 Infrastructure & Multi-DC":
    st.markdown("### Multi-DC Infrastructure & Edge Simulation")
    st.caption("Simulate primary datacenter outages (DC-1 Mumbai), automatic failover to secondary datacenters (DC-2 Bengaluru), and edge node pre-filtering.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Data Center Outage Controls")
        dc_status = multi_dc.get_dc_status_summary()
        st.json(dc_status["datacenters"])

        if st.button("🚨 Simulate DC-1 (Mumbai) Outage"):
            res = multi_dc.simulate_dc_failure("dc1")
            st.error(f"Outage triggered: {res.get('action', '')}")

        if st.button("🟢 Recover DC-1 (Mumbai)"):
            res = multi_dc.recover_dc("dc1")
            st.success(f"Recovery: {res.get('action', '')}")

    with col2:
        st.markdown("#### Infrastructure Topology Diagram")
        infra_dsl = InfrastructureDSLParser.parse_yaml("")
        infra_dsl.datacenters["dc1"].status = multi_dc.config.datacenters["dc1"].status
        infra_dsl.datacenters["dc2"].status = multi_dc.config.datacenters["dc2"].status
        
        mermaid_topo = TopologyVisualizer.generate_mermaid(infra_dsl)
        st.markdown(f"```mermaid\n{mermaid_topo}\n```")


# Page 10: Reliability Lab
elif page == "🧪 Reliability Lab":
    st.markdown("### System Reliability & Performance Stress Lab")
    st.caption("Inject traffic load, provider failure rates, and network latency to measure auto-recovery rates and SLA compliance.")

    c1, c2, c3 = st.columns(3)
    load_tx = c1.slider("Simulated Workload (Transactions)", 50, 500, 150, 50)
    fail_rate = c2.slider("Provider Failure Rate (%)", 0, 50, 10, 5)
    lat_boost = c3.slider("Added Network Latency (ms)", 0, 300, 50, 10)

    if st.button("🧪 Run Benchmark Suite"):
        progress_bar = st.progress(0)
        results = []
        for i in range(load_tx):
            sim_p = "psp-a" if np.random.random() < (fail_rate / 100.0) else None
            out = engine.process_payment(amount=1000.0, simulate_failure_provider=sim_p)
            results.append(out)
            if i % 20 == 0:
                progress_bar.progress((i + 1) / load_tx)
        
        progress_bar.progress(1.0)
        
        succ_count = sum(1 for r in results if r.success)
        avg_l = sum(r.total_latency_ms for r in results) / len(results)
        
        st.success(f"Benchmark Complete! Processed {load_tx} transactions.")
        m1, m2, m3 = st.columns(3)
        m1.metric("Overall Success Rate", f"{(succ_count / load_tx)*100:.1f}%")
        m2.metric("Average Latency", f"{avg_l:.0f} ms")
        m3.metric("Auto-Recovered Retries", sum(r.retries_count for r in results))


# Page 11: API & Functional Core
elif page == "📚 API & Functional Core":
    st.markdown("### Architecture Specification & API Reference")
    
    st.markdown("#### System Architecture Topology")
    st.markdown("""
```mermaid
graph TD
    DSL[Declarative YAML DSL] --> Parser[DSL Parser & Validator]
    Parser --> Core[Python / Haskell Functional Core]
    Core --> Plan[Payment Execution Plan]
    Plan --> Router[Intelligent Payment Router]
    Router --> Health[Provider Health Tracker]
    Health --> Heal[Self-Healing Engine]
    Router --> PSPs[PSP Adapters: PSP-A / PSP-B / PSP-C]
    PSPs --> Telemetry[Telemetry & Anomaly Detector]
    Telemetry --> Storage[(SQLite Database)]
```
    """)

    st.markdown("#### Haskell Functional Core Specification")
    with open("functional-core/README.md", "r") as f:
        st.markdown(f.read())
