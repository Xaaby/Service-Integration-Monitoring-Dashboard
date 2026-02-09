-- Example views that can be used for more complex reporting or materialization.

CREATE OR REPLACE VIEW service_event_daily_agg AS
SELECT
    s.id AS service_id,
    s.environment,
    date_trunc('day', se.ts) AS day,
    COUNT(*) AS total_events,
    COUNT(*) FILTER (WHERE se.status = 'success') AS success_events,
    COUNT(*) FILTER (WHERE se.status = 'failure') AS failure_events,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY se.latency_ms)
        FILTER (WHERE se.event_type = 'request' AND se.latency_ms IS NOT NULL) AS p50_latency,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY se.latency_ms)
        FILTER (WHERE se.event_type = 'request' AND se.latency_ms IS NOT NULL) AS p95_latency
FROM service_events se
JOIN services s ON s.id = se.service_id
GROUP BY s.id, s.environment, date_trunc('day', se.ts);

