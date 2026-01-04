from __future__ import annotations

import fnmatch
from collections.abc import Iterable
from copy import deepcopy
from functools import reduce
from operator import getitem
from typing import Any, Protocol, runtime_checkable

import asyncer
from attrs import define, field

from lsp_client.utils.uri import from_local_uri

Pattern = str
"""Glob pattern"""


def deep_merge(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively merge two dictionaries.
    """
    result = deepcopy(base)
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def deep_get(d: dict, keys: Iterable) -> Any:
    try:
        return reduce(getitem, keys, d)
    except (KeyError, TypeError):
        return None


@runtime_checkable
class ConfigurationChangeListener(Protocol):
    """
    Protocol for configuration change listeners.
    """

    async def __call__(self, config_map: ConfigurationMap) -> Any: ...


Config = dict[str, Any]
GlobalConfig = Config


@define
class ScopeConfig:
    """
    A helper class to represent a scope-specific configuration.
    """

    pattern: Pattern
    config: Config


@define
class ConfigurationMap:
    """
    A helper class to manage LSP configuration.
    Supports global configuration and scope-specific overrides.
    """

    global_config: GlobalConfig = field(factory=dict)
    scoped_configs: list[ScopeConfig] = field(factory=list)

    _on_change_callbacks: list[ConfigurationChangeListener] = field(
        factory=list, init=False
    )

    def on_change(self, callback: ConfigurationChangeListener) -> None:
        self._on_change_callbacks.append(callback)

    async def _notify_change(self) -> None:
        async with asyncer.create_task_group() as tg:
            for callback in self._on_change_callbacks:
                tg.soonify(callback)(self)

    async def update_global(
        self, config: dict[str, Any], *, merge: bool = True
    ) -> None:
        self.global_config = (
            deep_merge(self.global_config, config)  #
            if merge
            else deepcopy(config)
        )
        await self._notify_change()

    async def add_scope(self, pattern: Pattern, config: dict[str, Any]) -> None:
        """
        Add a configuration override for a specific file pattern.

        :param pattern: Glob pattern (e.g. "**/tests/**", "*.py")
        :param config: The configuration dict to merge for this scope
        """

        self.scoped_configs.append(ScopeConfig(pattern=pattern, config=config))
        await self._notify_change()

    def _get_section(self, config: Any, section: str | None) -> Any:
        if not section:
            return config

        return deep_get(config, section.split("."))

    def get(self, scope_uri: str | None, section: str | None) -> Any:
        final_config = self.global_config

        if not scope_uri:
            return self._get_section(final_config, section)

        path_str = from_local_uri(scope_uri).as_posix()
        for scope_config in self.scoped_configs:
            if not fnmatch.fnmatch(path_str, scope_config.pattern):
                continue
            final_config = deep_merge(final_config, scope_config.config)

        return self._get_section(final_config, section)
