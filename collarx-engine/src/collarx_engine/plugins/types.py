from enum import StrEnum


class PluginType(StrEnum):
    TELEPHONY = "telephony"
    AI_PROVIDER = "ai_provider"
    WORKFLOW_TOOL = "workflow_tool"
    INTEGRATION = "integration"
    CAMPAIGN_SOURCE = "campaign_source"
