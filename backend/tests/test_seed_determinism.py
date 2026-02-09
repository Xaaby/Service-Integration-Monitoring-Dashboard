from data.seed import generate_seed_events, SEED_VALUE


def test_seed_is_deterministic():
    services1, events1, incidents1 = generate_seed_events()
    services2, events2, incidents2 = generate_seed_events()

    assert SEED_VALUE == 42
    assert len(services1) == len(services2)
    assert len(events1) == len(events2)
    assert len(incidents1) == len(incidents2)

    # Spot check first event and incident for equality of key attributes
    assert events1[0].service.name == events2[0].service.name
    assert events1[0].ts == events2[0].ts
    assert events1[0].status == events2[0].status
    assert incidents1[0].summary == incidents2[0].summary

