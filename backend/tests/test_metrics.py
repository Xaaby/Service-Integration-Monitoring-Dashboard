from backend.app.metrics import calculate_health_score


def test_health_score_decreases_with_latency_and_errors():
    base = calculate_health_score(p95_latency=200, error_rate_per_1k=1)
    worse_latency = calculate_health_score(p95_latency=1200, error_rate_per_1k=1)
    worse_errors = calculate_health_score(p95_latency=200, error_rate_per_1k=60)

    assert worse_latency < base
    assert worse_errors < base

