"""Execute the real initialization methods with deterministic HA adapters."""

import ast
import asyncio
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest


class ConfigEntryNotReady(Exception):
    """Stand-in for the coordinator's retryable initial update failure."""


class ConfigEntryAuthFailed(Exception):
    """Authentication must never be hidden by optional-forecast handling."""


def init_method():
    source = Path(__file__).parents[1] / "custom_components/tianqi/__init__.py"
    tree = ast.parse(source.read_text())
    client = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "TianqiClient"
    )
    method = next(
        node
        for node in client.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "init"
    )
    module = ast.Module(body=[method], type_ignores=[])
    scope = {
        "ConfigEntryNotReady": ConfigEntryNotReady,
        "_LOGGER": logging.getLogger(__name__),
    }
    exec(compile(module, str(source), "exec"), scope)  # noqa: S102 - trusted repository method, not user input
    return scope["init"]


def coordinator(name, error=None):
    return SimpleNamespace(
        name=name,
        async_add_listener=Mock(return_value=Mock()),
        async_config_entry_first_refresh=AsyncMock(side_effect=error),
    )


def test_optional_minutely_outage_does_not_block_setup_or_remove_its_retry_listener():
    summary = coordinator("summary")
    minute = coordinator("minutely", ConfigEntryNotReady("temporarily offline"))
    client = SimpleNamespace(
        station=True, coordinators=[summary, minute], _remove_listeners=[]
    )
    asyncio.run(init_method()(client))
    assert len(client._remove_listeners) == 2
    summary.async_config_entry_first_refresh.assert_awaited_once()
    minute.async_add_listener.assert_called_once()


@pytest.mark.parametrize("name", ["summary", "observe", "hourlies", "dailies"])
def test_required_forecasts_still_request_setup_retry(name):
    client = SimpleNamespace(
        station=True,
        coordinators=[coordinator(name, ConfigEntryNotReady())],
        _remove_listeners=[],
    )
    with pytest.raises(ConfigEntryNotReady):
        asyncio.run(init_method()(client))


@pytest.mark.parametrize(
    "error", [ConfigEntryAuthFailed(), TypeError("implementation bug")]
)
def test_minutely_does_not_swallow_authentication_or_programming_errors(error):
    client = SimpleNamespace(
        station=True,
        coordinators=[coordinator("minutely", error)],
        _remove_listeners=[],
    )
    with pytest.raises(type(error)):
        asyncio.run(init_method()(client))
