import streamlit as st
import pandas as pd

from dashboard.app import _fetch, select_service_and_filters


def main():
    st.title("Throughput Metrics")

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
    data = _fetch("/metrics/throughput", params=params)
    series = data.get("series", [])
    if not series:
        st.write("No throughput data for selected filters.")
        return

    df = pd.DataFrame(series)
    df["bucket"] = pd.to_datetime(df["bucket"])
    df = df.set_index("bucket")

    st.subheader("Throughput Over Time")
    st.line_chart(df[["throughput"]])

    # Simple heatmap-style view (weekday vs hour)
    df_heat = df.copy()
    df_heat["weekday"] = df_heat.index.weekday
    df_heat["hour"] = df_heat.index.hour
    pivot = df_heat.pivot_table(
        index="weekday",
        columns="hour",
        values="throughput",
        aggfunc="sum",
        fill_value=0,
    )
    st.subheader("Throughput Heatmap (weekday x hour)")
    st.dataframe(pivot.style.background_gradient(cmap="Blues"))


if __name__ == "__main__":
    main()

