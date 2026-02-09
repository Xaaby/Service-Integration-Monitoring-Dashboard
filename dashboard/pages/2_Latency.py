import streamlit as st
import pandas as pd

from dashboard.app import _fetch, select_service_and_filters


def main():
    st.title("Latency Metrics")

    svc, env, (from_ts, to_ts) = select_service_and_filters()
    if not svc:
        return

    params = {
        "service_id": svc["id"],
        "env": env,
        "from": from_ts,
        "to": to_ts,
        "bucket": "day",
    }
    data = _fetch("/metrics/latency", params=params)
    series = data.get("series", [])
    if not series:
        st.write("No latency data for selected filters.")
        return

    df = pd.DataFrame(series)
    df["bucket"] = pd.to_datetime(df["bucket"])
    df = df.set_index("bucket")

    st.line_chart(df[["p50_latency", "p95_latency"]])

    # Simple regression marker: highlight last week vs earlier
    if len(df) > 7:
        recent_p95 = df["p95_latency"].tail(7).mean()
        prev_p95 = df["p95_latency"].iloc[:-7].mean()
        if recent_p95 > prev_p95 * 1.2:
            st.warning(
                f"Latency regression detected: recent p95 ({recent_p95:.0f} ms) "
                f"is more than 20% higher than earlier ({prev_p95:.0f} ms)."
            )


if __name__ == "__main__":
    main()

