"""
PayWeave — Declarative Payment Application & Intelligent Infrastructure Framework.
Main Streamlit Application Entrypoint.
Exposes full framework features: Merchant Console, Low-Code Flow Builder, Intelligent Router,
Self-Healing, Anomaly Detection, AI Ops, Multi-DC Infrastructure, and Reliability Lab.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time

from payweave.dsl.schema import MerchantConfig, RoutingStrategy, AuthMode, UILayout, UITheme
from payweave.dsl.parser import DSLParser
from payweave.dsl.validator import DSLValidator
from payweave.runtime.engine import PayWeaveEngine
from payweave.runtime.functional_core import PaymentRequest
from payweave.anomaly.detector import AnomalyDetector
from payweave.anomaly.simulator import TelemetrySimulator
from payweave.aiops.payment_assist import PayWeaveAssist
from payweave.aiops.incident_analyzer import IncidentAnalyzer
from payweave.infrastructure.infrastructure_dsl import InfrastructureDSLParser
from payweave.infrastructure.topology import TopologyVisualizer
from payweave.infrastructure.multi_dc import MultiDCSimulator
from payweave.infrastructure.edge import EdgeComputingSimulator
from payweave.analytics.metrics import MetricsCollector
from payweave.analytics.aggregations import AnalyticsAggregator

# Page Configuration
st.set_page_config(
    page_title="PayWeave Framework",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Styling for Glassmorphic Fintech UI
st.markdown("""
<style>
    /* Dark glassmorphic background & typography */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    
    /* Header Banner */
    .main-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    }
    
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #818CF8 0%, #C084FC 50%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    
    .subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        font-weight: 500;
    }
    
    /* KPI Card styling */
    .kpi-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .kpi-title {
        color: #94A3B8;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 1.7rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 4px;
    }

    /* Disclaimer alert */
    .disclaimer-banner {
        background: rgba(245, 158, 11, 0.1);
        border-left: 4px solid #F59E0B;
        padding: 10px 16px;
        border-radius: 6px;
        font-size: 0.85rem;
        color: #FCD34D;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State Singleton Engine
if "engine" not in st.session_state:
    st.session_state.engine = PayWeaveEngine()

if "multi_dc" not in st.session_state:
    st.session_state.multi_dc = MultiDCSimulator()

if "edge_sim" not in st.session_state:
    st.session_state.edge_sim = EdgeComputingSimulator()

if "telemetry" not in st.session_state:
    st.session_state.telemetry = TelemetrySimulator.generate_telemetry_stream(num_records=50)

engine = st.session_state.engine
multi_dc = st.session_state.multi_dc
edge_sim = st.session_state.edge_sim


# Sidebar Navigation
st.sidebar.markdown("## ⚡ PayWeave Engine")
st.sidebar.caption("Declarative Payment & Infrastructure Framework")

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
st.sidebar.markdown("### 🔧 Quick Actions")
if st.sidebar.button("🔄 Reset Simulation Data", use_container_width=True):
    engine.reset_simulation()
    multi_dc.recover_dc("dc1")
    multi_dc.recover_dc("dc2")
    st.session_state.telemetry = TelemetrySimulator.generate_telemetry_stream(num_records=50)
    st.sidebar.success("Simulation state reset!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='font-size: 11px; color: #64748B; text-align: center;'>"
    "PayWeave Portfolio Framework v1.0<br>"
    "Simulated Infrastructure & Metrics"
    "</div>",
    unsafe_allow_html=True
)

# Header Banner across all pages
st.markdown("""
<div class="main-header">
    <div class="main-title">PAYWEAVE</div>
    <div class="subtitle">Declarative Payment Application & Intelligent Infrastructure Framework</div>
</div>
<div class="disclaimer-banner">
    ⚠️ <b>Portfolio Simulation Disclaimer:</b> PayWeave is an architectural demonstration framework.
    It uses synthetic workloads and simulated payment providers. It does NOT process real money or handle real customer payment credentials.
</div>
""", unsafe_allow_html=True)


# Page 1: Home & Overview
if page == "🏠 Home & Overview":
    st.markdown("### System KPI Overview")
    
    health_map = engine.get_provider_health_map()
    succ_rates = [h.success_rate for h in health_map.values()]
    avg_succ = (sum(succ_rates) / len(succ_rates)) * 100 if succ_rates else 99.1
    active_providers = sum(1 for h in health_map.values() if h.is_healthy)
    healing_events = len(engine.self_healing.events)
    
    # Calculate anomaly count
    detector = AnomalyDetector()
    anomalies = detector.detect_batch_anomalies(st.session_state.telemetry)
    anomaly_count = sum(1 for a in anomalies if a.anomaly_detected)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(f'<div class="kpi-card"><div class="kpi-title">System Health</div><div class="kpi-value" style="color:#10B981">{avg_succ:.1f}%</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card"><div class="kpi-title">Active Providers</div><div class="kpi-value" style="color:#38BDF8">{active_providers} / 3</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card"><div class="kpi-title">Routing Mode</div><div class="kpi-value" style="color:#C084FC">{engine.config.routing.strategy.upper()}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card"><div class="kpi-title">Anomalies Detected</div><div class="kpi-value" style="color:#F59E0B">{anomaly_count}</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="kpi-card"><div class="kpi-title">Self-Healing Events</div><div class="kpi-value" style="color:#6366F1">{healing_events}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Real-time Synthetic Transaction Volume & Success Rate")
        df_telem = pd.DataFrame(st.session_state.telemetry)
        
        fig_vol = px.line(
            df_telem,
            x="formatted_time",
            y="transaction_count",
            color="provider",
            title="Transaction Throughput by Provider (tx/min)",
            color_discrete_sequence=["#818CF8", "#38BDF8", "#F59E0B"]
        )
        fig_vol.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC")
        st.plotly_chart(fig_vol, use_container_width=True)

    with col2:
        st.markdown("#### Provider Health & Latency SLA Matrix")
        df_comp = AnalyticsAggregator.build_provider_comparison_df(health_map)
        st.dataframe(df_comp, hide_index=True, use_container_width=True)

        st.markdown("#### Operational Summary")
        analyzer = IncidentAnalyzer()
        summary_text = analyzer.generate_operational_summary(health_map, engine.self_healing.get_timeline(), anomaly_count)
        st.info(summary_text)


# Page 2: Merchant Console
elif page == "🎛️ Merchant Console":
    st.markdown("### Merchant Console & Self-Service Portal")
    st.caption("Customize payment behavior, risk thresholds, and checkout page styling declaratively without changing code.")

    tabs = st.tabs(["📋 General & Payment", "🔀 Routing & Fallback", "🛡️ Risk & Auth", "🎨 Checkout UI", "📄 Export YAML DSL", "📜 Audit Log"])

    with tabs[0]:
        st.markdown("#### Merchant Information & Methods")
        m_name = st.text_input("Merchant Name", engine.config.merchant.name)
        m_id = st.text_input("Merchant ID", engine.config.merchant.id)
        selected_methods = st.multiselect("Supported Payment Methods", ["upi", "card", "netbanking"], engine.config.payment.methods)
        
        if st.button("Save General Settings"):
            engine.config.merchant.name = m_name
            engine.config.merchant.id = m_id
            engine.config.payment.methods = selected_methods
            engine.reload_config(engine.config)
            st.success("Merchant parameters updated!")

    with tabs[1]:
        st.markdown("#### Routing Strategy & Fallback Rules")
        strat = st.selectbox(
            "Routing Strategy",
            ["intelligent", "highest_success_rate", "lowest_latency", "lowest_cost", "balanced"],
            index=0
        )
        fallback_enabled = st.checkbox("Enable Provider Fallback", engine.config.routing.fallback.enabled)
        max_retries = st.slider("Max Retries Before Failure", 0, 5, engine.config.routing.fallback.max_retries)

        if st.button("Save Routing Configuration"):
            engine.config.routing.strategy = RoutingStrategy(strat)
            engine.config.routing.fallback.enabled = fallback_enabled
            engine.config.routing.fallback.max_retries = max_retries
            engine.reload_config(engine.config)
            st.success("Routing policies saved!")

    with tabs[2]:
        st.markdown("#### Risk Thresholds & Authentication Mode")
        r_max = st.slider("Max Allowed Risk Score (0.0 - 1.0)", 0.1, 1.0, float(engine.config.risk.max_score), 0.05)
        block_high = st.checkbox("Automatically Block High Risk Transactions", engine.config.risk.block_high_risk)
        
        auth_mode = st.selectbox("Authentication Security Mode", ["adaptive", "frictionless", "always_2fa"], index=0)
        step_up_th = st.slider("Step-up 2FA Risk Threshold", 0.1, 1.0, float(engine.config.authentication.step_up_threshold), 0.05)

        if st.button("Save Risk & Security Policy"):
            engine.config.risk.max_score = r_max
            engine.config.risk.block_high_risk = block_high
            engine.config.authentication.mode = AuthMode(auth_mode)
            engine.config.authentication.step_up_threshold = step_up_th
            engine.reload_config(engine.config)
            st.success("Security policies saved!")

    with tabs[3]:
        st.markdown("#### Declarative Checkout UI Customization")
        brand = st.text_input("Brand Display Name", engine.config.payment_page.brand_name)
        color = st.color_picker("Primary Brand Accent Color", engine.config.payment_page.primary_color)
        layout_choice = st.selectbox("UI Layout Mode", ["compact", "standard", "expanded"])
        theme_choice = st.selectbox("UI Theme", ["vibrant_fintech", "dark_glass", "light_corporate", "minimal"])

        if st.button("Apply UI Configuration"):
            engine.config.payment_page.brand_name = brand
            engine.config.payment_page.primary_color = color
            engine.reload_config(engine.config)
            st.success("Checkout UI configuration updated!")

    with tabs[4]:
        st.markdown("#### Declarative YAML DSL Specification")
        yaml_out = DSLParser.to_yaml(engine.config)
        st.code(yaml_out, language="yaml")

    with tabs[5]:
        st.markdown("#### Merchant Configuration Audit Log")
        audit_logs = engine.db.get_audit_logs()
        if audit_logs:
            st.dataframe(pd.DataFrame(audit_logs), use_container_width=True)
        else:
            st.info("No audit entries recorded yet.")


# Page 3: Flow Builder (Low-Code / No-Code)
elif page == "🧩 Flow Builder (Low-Code)":
    st.markdown("### Visual Low-Code Payment Flow Builder")
    st.caption("Construct payment execution pipelines visually. Changes generate Declarative YAML DSL automatically.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Interactive Visual Pipeline Nodes")
        
        # Interactive Node Configuration Form
        risk_node = st.slider("Risk Check Node: Max Score", 0.1, 1.0, float(engine.config.risk.max_score), 0.05)
        auth_node = st.selectbox("Auth Node: Security Mode", ["adaptive", "frictionless", "always_2fa"])
        route_node = st.selectbox("Route Node: Strategy", ["intelligent", "highest_success_rate", "lowest_latency", "lowest_cost"])
        retry_node = st.number_input("Fallback Node: Max Retries", 0, 5, engine.config.routing.fallback.max_retries)

        if st.button("⚡ Update Flow Graph & Regenerate DSL"):
            engine.config.risk.max_score = risk_node
            engine.config.authentication.mode = AuthMode(auth_node)
            engine.config.routing.strategy = RoutingStrategy(route_node)
            engine.config.routing.fallback.max_retries = retry_node
            engine.reload_config(engine.config)
            st.success("Flow graph compiled into active runtime!")

    with col2:
        st.markdown("#### Generated Visual Pipeline Diagram")
        flow_nodes = DSLParser.config_to_flow_nodes(engine.config)
        
        # Build Mermaid graph
        mermaid_lines = ["graph TD"]
        for i in range(len(flow_nodes) - 1):
            curr = flow_nodes[i]
            nxt = flow_nodes[i+1]
            mermaid_lines.append(f"    {curr['id']}[\"<b>{curr['label']}</b><br><small>{curr['description']}</small>\"] --> {nxt['id']}[\"<b>{nxt['label']}</b><br><small>{nxt['description']}</small>\"]")
        
        st.markdown(f"```mermaid\n{chr(10).join(mermaid_lines)}\n```")

    st.markdown("---")
    st.markdown("#### Bidirectional YAML Code Preview")
    st.code(DSLParser.to_yaml(engine.config), language="yaml")


# Page 4: Payment Simulator
elif page == "💳 Payment Simulator":
    st.markdown("### Interactive Payment Request Simulator")
    st.caption("Execute simulated transactions against the PayWeave runtime engine to observe step-by-step validation, risk scoring, intelligent routing, and fallback.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Transaction Input")
        sim_amt = st.number_input("Transaction Amount (₹)", min_value=1.0, value=2500.0, step=100.0)
        sim_method = st.selectbox("Payment Method", engine.config.payment.methods)
        sim_curr = st.selectbox("Currency", engine.config.payment.currencies)
        sim_risk = st.slider("Simulated Customer Risk Score", 0.0, 1.0, 0.10, 0.05)
        
        force_fail = st.selectbox(
            "Inject Synthetic Provider Failure (Testing)",
            ["None", "psp-a", "psp-b", "psp-c"],
            help="Forces a specific provider to decline/timeout to test fallback rerouting."
        )
        fail_provider = None if force_fail == "None" else force_fail

        if st.button("🚀 Process Simulated Payment", use_container_width=True):
            with st.spinner("Executing functional payment pipeline..."):
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
    st.caption("Multi-factor dynamic scoring engine ranking PSP adapters by success rate, latency, provider health, cost score, and capacity.")

    health_map = engine.get_provider_health_map()
    
    st.markdown("#### Live Provider Health & Scoring Metrics")
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
        font_color="#F8FAFC"
    )
    st.plotly_chart(fig_radar, use_container_width=True)


# Page 6: Self-Healing System
elif page == "🛡️ Self-Healing System":
    st.markdown("### Self-Healing & Automated Circuit Breaker System")
    st.caption("Detects provider degradation, automatically reduces health scores, shifts live traffic to healthy fallbacks, and records recovery audit timelines.")

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
        st.markdown("#### Self-Healing Event Recovery Timeline")
        timeline = engine.self_healing.get_timeline()
        if timeline:
            for ev in timeline:
                sev_color = "#EF4444" if ev["severity"] == "CRITICAL" else "#F59E0B" if ev["severity"] == "WARNING" else "#10B981"
                st.markdown(
                    f"<div style='border-left: 3px solid {sev_color}; padding-left: 10px; margin-bottom: 12px; background: rgba(30,41,59,0.5); padding: 8px 12px; border-radius: 4px;'>"
                    f"<b>[{ev['time']}] {ev['event_type']} ({ev['provider_id'].upper()})</b><br>"
                    f"<small>{ev['description']}</small><br>"
                    f"<span style='color: #38BDF8;'>Action: {ev['action_taken']}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No self-healing events recorded yet. Trigger a degradation event to observe automated recovery.")


# Page 7: Anomaly Detection
elif page == "📈 Anomaly Detection":
    st.markdown("### Automatic Payment Telemetry Anomaly Detector")
    st.caption("Uses rolling Z-score statistical analysis to detect latency spikes, success rate drops, and error bursts.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### Anomaly Injection & Sensitivity")
        inject_psp = st.selectbox("Inject Synthetic Anomaly into Stream", ["None", "psp-a", "psp-b", "psp-c"])
        inj_target = None if inject_psp == "None" else inject_psp
        
        sensitivity = st.slider("Anomaly Alert Threshold", 0.3, 0.9, 0.65, 0.05)

        if st.button("⚡ Regenerate Telemetry Batch"):
            st.session_state.telemetry = TelemetrySimulator.generate_telemetry_stream(
                num_records=50, inject_anomaly_provider=inj_target
            )
            st.success("New telemetry batch generated!")

    with col2:
        detector = AnomalyDetector()
        reports = detector.detect_batch_anomalies(st.session_state.telemetry, sensitivity_threshold=sensitivity)

        st.markdown("#### Anomaly Detection Diagnostic Reports")
        for r in reports:
            if r.anomaly_detected:
                st.error(f"🚨 **{r.severity} ANOMALY DETECTED ({r.affected_provider.upper()})** - Score: {r.anomaly_score:.2f}\n\n{r.explanation}")
            else:
                st.success(f"🟢 **NORMAL OPERATIONS ({r.affected_provider.upper()})** - Score: {r.anomaly_score:.2f}\n\n{r.explanation}")

    st.markdown("---")
    st.markdown("#### Telemetry Latency & Error Streams")
    df_t = pd.DataFrame(st.session_state.telemetry)
    fig_lat = px.line(df_t, x="formatted_time", y="latency", color="provider", title="Live Telemetry Latency Stream (ms)")
    fig_lat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC")
    st.plotly_chart(fig_lat, use_container_width=True)


# Page 8: AI Payment Operations
elif page == "🤖 AI Payment Operations":
    st.markdown("### PayWeave Assist — AI Operations Panel")
    st.caption("Ask questions about live payment performance, routing decisions, provider outages, and cost optimization. Works 100% offline with deterministic fallback.")

    assist = PayWeaveAssist()
    health_map = engine.get_provider_health_map()
    recent_events = engine.self_healing.get_timeline()

    st.markdown("#### Ask PayWeave Assist")
    sample_queries = [
        "Why did PSP-A lose traffic?",
        "Which provider is currently healthiest?",
        "What caused the latency spike?",
        "What would happen if DC-1 failed?",
        "Which routing strategy minimizes cost?"
    ]
    
    selected_query = st.selectbox("Sample Questions", sample_queries)
    custom_query = st.text_input("Or type custom question:", selected_query)

    if st.button("🤖 Generate AI Analysis"):
        with st.spinner("Analyzing operational telemetry..."):
            ans = assist.ask(custom_query, engine.config, health_map, recent_events)
            st.markdown("---")
            st.markdown(ans)


# Page 9: Infrastructure & Multi-DC
elif page == "🌐 Infrastructure & Multi-DC":
    st.markdown("### Distributed Infrastructure & Multi-DC Simulation")
    st.caption("Simulate primary datacenter outages (DC-1 Mumbai), failover to secondary datacenters (DC-2 Bengaluru), and edge node evaluation.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Data Center Outage Simulator")
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
        # reflect current simulation status in dsl
        infra_dsl.datacenters["dc1"].status = multi_dc.config.datacenters["dc1"].status
        infra_dsl.datacenters["dc2"].status = multi_dc.config.datacenters["dc2"].status
        
        mermaid_topo = TopologyVisualizer.generate_mermaid(infra_dsl)
        st.markdown(f"```mermaid\n{mermaid_topo}\n```")


# Page 10: Reliability Lab
elif page == "🧪 Reliability Lab":
    st.markdown("### System Reliability & Performance Stress Lab")
    st.caption("Inject traffic load, provider failure rates, and network latency to measure recovery rates and SLA compliance.")

    c1, c2, c3 = st.columns(3)
    load_tx = c1.slider("Simulated Workload (Transactions)", 50, 1000, 200, 50)
    fail_rate = c2.slider("Provider Failure Rate (%)", 0, 50, 10, 5)
    lat_boost = c3.slider("Added Network Latency (ms)", 0, 300, 50, 10)

    if st.button("🧪 Run Reliability Benchmark Suite"):
        progress_bar = st.progress(0)
        results = []
        for i in range(load_tx):
            sim_p = "psp-a" if random.random() < (fail_rate / 100.0) else None
            out = engine.process_payment(amount=1000.0, simulate_failure_provider=sim_p)
            results.append(out)
            if i % 20 == 0:
                progress_bar.progress((i + 1) / load_tx)
        
        progress_bar.progress(1.0)
        
        succ_count = sum(1 for r in results if r.success)
        avg_l = sum(r.total_latency_ms for r in results) / len(results)
        
        st.success(f"Benchmark Complete! Processed {load_tx} transactions.")
        m1, m2, m3 = st.columns(3)
        m1.metric("Success Rate", f"{(succ_count / load_tx)*100:.1f}%")
        m2.metric("Average Latency", f"{avg_l:.0f} ms")
        m3.metric("Auto-Recovered Retries", sum(r.retries_count for r in results))


# Page 11: API & Functional Core
elif page == "📚 API & Functional Core":
    st.markdown("### Architecture Specification & API Reference")
    
    st.markdown("#### System Architecture Diagram")
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
