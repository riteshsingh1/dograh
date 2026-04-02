from abc import ABC
from dataclasses import dataclass
from typing import Any

from collarx_engine.plugins.types import PluginType


@dataclass
class PluginContext:
    settings: dict[str, Any]


class CollarxPlugin(ABC):
    name: str
    version: str
    plugin_type: PluginType

    def on_register(self, context: PluginContext) -> None:
        return None

    async def on_startup(self) -> None:
        return None

    async def on_shutdown(self) -> None:
        return None


class TelephonyPlugin(CollarxPlugin):
    plugin_type = PluginType.TELEPHONY

    def create_provider(self, config: dict[str, Any]) -> Any:
        raise NotImplementedError


class AIProviderPlugin(CollarxPlugin):
    plugin_type = PluginType.AI_PROVIDER

    def create_stt(self, config: dict[str, Any]) -> Any:
        raise NotImplementedError

    def create_tts(self, config: dict[str, Any]) -> Any:
        raise NotImplementedError

    def create_llm(self, config: dict[str, Any]) -> Any:
        raise NotImplementedError


class WorkflowToolPlugin(CollarxPlugin):
    plugin_type = PluginType.WORKFLOW_TOOL

    async def execute(self, context: dict[str, Any], params: dict[str, Any]) -> Any:
        raise NotImplementedError


class IntegrationPlugin(CollarxPlugin):
    plugin_type = PluginType.INTEGRATION

    async def on_call_complete(self, run_data: dict[str, Any]) -> None:
        return None


class CampaignSourcePlugin(CollarxPlugin):
    plugin_type = PluginType.CAMPAIGN_SOURCE

    async def sync(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        raise NotImplementedError
