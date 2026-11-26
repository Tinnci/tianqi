"""Regression for provider timestamps with optional seconds in upstream client."""

import ast
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest


def load_parse_observe_time():
    source = Path(__file__).parents[1] / "custom_components/tianqi/client.py"
    tree = ast.parse(source.read_text())
    wanted = {"_parse_datetime", "_parse_observe_time"}
    nodes = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in wanted
    ]
    module = ast.Module(body=nodes, type_ignores=[])
    scope = {
        "Any": Any,
        "datetime": datetime,
        "OBSERVE_TIME_FORMAT": "%Y%m%d%H%M",
        "OBSERVE_TIME_FORMATS": ("%Y%m%d%H%M", "%Y%m%d%H%M%S"),
    }
    exec(compile(module, str(source), "exec"), scope)  # noqa: S102 - trusted repository helper, not user input
    return scope["_parse_observe_time"]


parse = load_parse_observe_time()


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
    "value", [None, "", "20261303090000", "２０２６１００３０９００"]
)
def test_invalid_input_returns_none(value):
    assert parse(value) is None
