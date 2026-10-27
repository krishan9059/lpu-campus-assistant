from app.core.rate_limit import SlidingWindowLimiter


def test_allows_up_to_the_limit():
    clock = [0.0]
    limiter = SlidingWindowLimiter(3, window_seconds=60, clock=lambda: clock[0])
    assert limiter.check("a") == 0
    assert limiter.check("a") == 0
    assert limiter.check("a") == 0


def test_blocks_beyond_the_limit():
    clock = [0.0]
    limiter = SlidingWindowLimiter(2, window_seconds=60, clock=lambda: clock[0])
    limiter.check("a")
    limiter.check("a")
    assert limiter.check("a") > 0


def test_window_slides_and_frees_up_slots():
    clock = [0.0]
    limiter = SlidingWindowLimiter(1, window_seconds=10, clock=lambda: clock[0])
    limiter.check("a")
    assert limiter.check("a") > 0
    clock[0] = 11.0
    assert limiter.check("a") == 0


def test_keys_are_independent():
    clock = [0.0]
    limiter = SlidingWindowLimiter(1, window_seconds=60, clock=lambda: clock[0])
    limiter.check("a")
    assert limiter.check("b") == 0
