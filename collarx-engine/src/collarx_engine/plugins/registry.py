from importlib.metadata import entry_points
from typing import Iterable

from collarx_engine.plugins.base import CollarxPlugin, PluginContext
from collarx_engine.plugins.types import PluginType


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[PluginType, dict[str, CollarxPlugin]] = {
            plugin_type: {} for plugin_type in PluginType
        }

    def register(self, plugin: CollarxPlugin, context: PluginContext | None = None) -> None:
        plugin_map = self._plugins[plugin.plugin_type]
        plugin_map[plugin.name] = plugin
        if context:
            plugin.on_register(context)

    def get(self, plugin_type: PluginType, name: str) -> CollarxPlugin | None:
        return self._plugins[plugin_type].get(name)

    def list(self, plugin_type: PluginType | None = None) -> Iterable[CollarxPlugin]:
        if plugin_type is not None:
            return self._plugins[plugin_type].values()
        all_plugins: list[CollarxPlugin] = []
        for typed_plugins in self._plugins.values():
            all_plugins.extend(typed_plugins.values())
        return all_plugins

    def discover_and_register(self, context: PluginContext | None = None) -> None:
        for ep in entry_points(group="collarx.plugins"):
            plugin_cls = ep.load()
            plugin = plugin_cls()
            self.register(plugin, context=context)
