from collections import defaultdict, deque
from functools import wraps
from time import monotonic

from fastapi import HTTPException, Request


class Limiter:
    def __init__(self):
        self._events = defaultdict(deque)

    def reset(self):
        self._events.clear()

    def limit(self, specification):
        amount, period = specification.split("/", 1)
        maximum = int(amount)

        if period.endswith("minutes"):
            seconds = int(period.removesuffix("minutes")) * 60
        else:
            seconds = int(period.removesuffix("seconds"))

        def decorator(function):
            @wraps(function)
            def wrapped(*args, **kwargs):
                request = kwargs.get("request") or next(
                    (arg for arg in args if isinstance(arg, Request)),
                    None,
                )

                if request is not None:
                    key = (
                        request.client.host if request.client else "unknown",
                        request.url.path,
                    )
                    now = monotonic()
                    events = self._events[key]

                    while events and now - events[0] >= seconds:
                        events.popleft()

                    if len(events) >= maximum:
                        raise HTTPException(
                            status_code=429,
                            detail="Too many requests. Please try again later.",
                        )

                    events.append(now)

                return function(*args, **kwargs)

            return wrapped

        return decorator


limiter = Limiter()
