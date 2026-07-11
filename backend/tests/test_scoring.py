from app.visibility import scoring


def test_retrieval_signal_takes_best_hit():
    assert scoring.retrieval_signal([{"score": 0.2}, {"score": 0.7}]) == 0.7
    assert scoring.retrieval_signal([]) == 0.0


def test_reasoning_signal_saturates():
    assert scoring.reasoning_signal(0, 0) == 0.0
    assert scoring.reasoning_signal(2, 2) == 1.0     # 4/4
    assert scoring.reasoning_signal(10, 10) == 1.0   # capped


def test_trust_signal_defaults_when_no_claims():
    assert scoring.trust_signal(None) == 0.3
    assert scoring.trust_signal(0.9) == 0.9


def test_machine_readability_penalizes_blocked_and_unstructured():
    open_site = [{"http_status": 200, "has_schema_org": True,
                  "ai_crawler_policy": {"bots": {"GPTBot": "allowed"}}}]
    blocked_site = [{"http_status": 200, "has_schema_org": False,
                     "ai_crawler_policy": {"bots": {"GPTBot": "blocked"}}}]
    assert scoring.machine_readability_signal(open_site) == 1.0
    # crawlable (0.4) but AI-blocked (0) and no schema (0) -> 0.4
    assert scoring.machine_readability_signal(blocked_site) == 0.4
    assert scoring.machine_readability_signal([]) == 0.0


def test_overall_is_mean_of_four():
    assert scoring.overall(1.0, 1.0, 1.0, 1.0) == 100
    assert scoring.overall(0.5, 0.5, 0.5, 0.5) == 50
    assert scoring.overall(0.0, 0.0, 0.0, 0.0) == 0
