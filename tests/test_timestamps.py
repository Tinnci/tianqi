"""Regression for the provider adding seconds to observe and forecast timestamps."""

import runpy
from datetime import datetime
from pathlib import Path

import pytest

parse = runpy.run_path(
    str(Path(__file__).parents[1] / "custom_components/tianqi/timestamps.py")
)["parse_provider_timestamp"]


@pytest.mark.parametrize(
    "value,expected",
    [
        ("202610030900", datetime(2026, 10, 3, 9)),
        ("20261003090000", datetime(2026, 10, 3, 9)),
        ("20261231235945", datetime(2026, 12, 31, 23, 59, 45)),
    ],
)
def test_both_provider_formats(value, expected):
    assert parse(value) == expected


@pytest.mark.parametrize(
    "value", [None, "", "20261303090000", "202610030900000", "２０２６１００３０９００"]
)
def test_invalid_input_is_not_silently_truncated(value):
    with pytest.raises(ValueError):
        parse(value)
