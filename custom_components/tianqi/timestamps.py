"""Parse provider timestamps without discarding their seconds."""

from datetime import datetime


def parse_provider_timestamp(value: str) -> datetime:
    if (
        not isinstance(value, str)
        or len(value) not in (12, 14)
        or not value.isascii()
        or not value.isdigit()
    ):
        raise ValueError("Expected a 12- or 14-digit provider timestamp")
    # Keep the provider's local clock semantics used by the existing consumers.
    return datetime.strptime(  # noqa: DTZ007
        value, "%Y%m%d%H%M%S" if len(value) == 14 else "%Y%m%d%H%M"
    )
