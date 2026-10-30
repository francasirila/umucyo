from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc)


def ensure_aware(value):
    if value is None:
        return None

    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def enum_value(value):
    return getattr(value, "value", value)
