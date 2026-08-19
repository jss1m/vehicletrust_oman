from vehicletrust.services import run_scenario


def test_expired_challenge_is_rejected_without_sleep(ctx):
    result = run_scenario("expiry")
    assert result["actual"] == "EXPIRED_CHALLENGE"


def test_challenge_before_expiry_passes(ctx):
    assert run_scenario("normal")["actual"] == "VERIFIED"
