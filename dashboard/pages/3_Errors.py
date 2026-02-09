import streamlit as st
import pandas as pd

from dashboard.app import _fetch, select_service_and_filters


def main():
    st.title("Error Metrics")

    svc, env, (from_ts, to_ts) = select_service_and_filters()
    if not svc:
        return

    params = {
        "service_id": svc["id"],
        "env": env,
        "from": from_ts,
        "to": to_ts,
    }
    data = _fetch("/metrics/errors", params=params)

    top_codes = data.get("top_error_codes", [])
    if top_codes:
        st.subheader("Top Error Codes")
        df_codes = pd.DataFrame(top_codes)
        st.bar_chart(df_codes.set_index("error_code"))
    else:
        st.write("No error codes for selected filters.")

    series = data.get("failures_timeseries", [])
    if series:
        st.subheader("Failures Over Time")
        df_series = pd.DataFrame(series)
        df_series["bucket"] = pd.to_datetime(df_series["bucket"])
        df_series = df_series.set_index("bucket")
        st.line_chart(df_series[["failures"]])


if __name__ == "__main__":
    main()

