import pytest
from fastapi import HTTPException, Request

from core import rate_limit
from core.rate_limit import Limiter


def make_request(path="/x", host="1.1.1.1"):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": [],
            "query_string": b"",
            "client": (host, 1234),
        }
    )


def build(limiter, spec="2/60seconds"):
    @limiter.limit(spec)
    def handler(request):
        return "ok"

    return handler


def test_allows_up_to_the_maximum_then_blocks():
    handler = build(Limiter())
    assert handler(make_request()) == "ok"
    assert handler(make_request()) == "ok"

    with pytest.raises(HTTPException) as exc:
        handler(make_request())
    assert exc.value.status_code == 429


def test_limits_are_tracked_per_client_and_path():
    handler = build(Limiter(), "1/60seconds")
    assert handler(make_request("/a", "1.1.1.1")) == "ok"
    assert handler(make_request("/a", "2.2.2.2")) == "ok"
    assert handler(make_request("/b", "1.1.1.1")) == "ok"


def test_window_expires(monkeypatch):
    clock = {"now": 1000.0}
    monkeypatch.setattr(rate_limit, "monotonic", lambda: clock["now"])

    handler = build(Limiter(), "1/10seconds")
    assert handler(make_request()) == "ok"

    with pytest.raises(HTTPException):
        handler(make_request())

    clock["now"] += 11
    assert handler(make_request()) == "ok"


def test_minutes_period_is_parsed(monkeypatch):
    clock = {"now": 0.0}
    monkeypatch.setattr(rate_limit, "monotonic", lambda: clock["now"])

    handler = build(Limiter(), "1/2minutes")
    handler(make_request())

    clock["now"] = 119
    with pytest.raises(HTTPException):
        handler(make_request())

    clock["now"] = 121
    assert handler(make_request()) == "ok"


def test_reset_clears_state():
    limiter = Limiter()
    handler = build(limiter, "1/60seconds")
    handler(make_request())
    limiter.reset()
    assert handler(make_request()) == "ok"


def test_function_without_request_is_not_limited():
    limiter = Limiter()

    @limiter.limit("1/60seconds")
    def handler():
        return "ok"

    assert handler() == "ok"
    assert handler() == "ok"
