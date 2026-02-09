import os
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")


def _fetch(path: str, params: dict | None = None):
    url = f"{API_BASE_URL}{path}"
    resp = requests.get(url, params=params or {}, timeout=10)
    resp.raise_for_status()
    return resp.json()


@st.cache_data(ttl=60)
def load_services():
    return _fetch("/services")


def select_service_and_filters():
    services = load_services()
    if not services:
        st.warning("No services found. Make sure the API and seed data are running.")
        return None, None, None

    svc_options = {s["name"]: s for s in services}
    selected_name = st.selectbox("Service", list(svc_options.keys()))
    selected_service = svc_options[selected_name]

    env = st.selectbox("Environment", ["prod", "stage"], index=0)

    default_to = datetime.utcnow().date()
    default_from = default_to - timedelta(days=7)
    date_range = st.date_input(
        "Date range",
        value=(default_from, default_to),
    )
    if isinstance(date_range, tuple):
        from_date, to_date = date_range
    else:
        from_date = date_range
        to_date = date_range

    from_ts = datetime.combine(from_date, datetime.min.time()).isoformat()
    to_ts = (datetime.combine(to_date, datetime.min.time()) + timedelta(days=1)).isoformat()

    return selected_service, env, (from_ts, to_ts)


def render_overview():
    st.title("Service Integration Monitoring Dashboard - Overview")

    svc, env, (from_ts, to_ts) = select_service_and_filters()
    if not svc:
        return

    params = {
        "service_id": svc["id"],
        "env": env,
        "from": from_ts,
        "to": to_ts,
    }
    data = _fetch("/metrics/overview", params=params)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Success Rate", f"{data['success_rate'] * 100:.1f}%")
    col2.metric("p95 Latency (ms)", f"{data['p95_latency']:.0f}" if data["p95_latency"] else "N/A")
    col3.metric("Throughput / day", f"{data['throughput_per_day']:.1f}")
    col4.metric("Errors / 1k", f"{data['error_rate_per_1k']:.1f}")

    health = data["health_score"]
    st.subheader("Health Score")
    st.progress(health / 100.0)
    st.write(f"**{health}/100**")

    # Incident notes
    st.subheader("Recent Incident Notes")
    notes = _fetch(f"/services/{svc['id']}/incidents")
    if not notes:
        st.write("No incident notes.")
    else:
        for n in notes:
            st.markdown(
                f"**{n['incident_date']}** — {n['summary']}  "
                f"_Root cause_: {n['root_cause']}  \n"
                f"_Resolution_: {n['resolution']}"
            )


if __name__ == "__main__":
    render_overview()

