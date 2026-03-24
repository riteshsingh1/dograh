import re
from typing import Any, Optional

import httpx
from loguru import logger

from api.db import db_client
from api.services.campaign.source_sync import (
    CampaignSourceSyncService,
    ValidationError,
    ValidationResult,
)


class MetaAdsSyncService(CampaignSourceSyncService):
    """Campaign source sync service for Meta Lead Ads."""

    graph_base = "https://graph.facebook.com/v23.0"

    async def validate_source(
        self,
        source_id: str,
        organization_id: Optional[int] = None,
        workflow_id: Optional[int] = None,
    ) -> ValidationResult:
        if not workflow_id:
            return ValidationResult(
                is_valid=False,
                error=ValidationError(message="workflow_id is required for meta-ads"),
            )

        try:
            config = await self._get_meta_config(workflow_id)
            access_token = (config.get("access_token") or "").strip()
            lead_form_id = self._normalize_lead_form_id(
                source_id or config.get("lead_form_id") or ""
            )
            if not access_token:
                return ValidationResult(
                    is_valid=False,
                    error=ValidationError(
                        message="Missing Meta access token in workflow campaign settings"
                    ),
                )
            if not lead_form_id:
                return ValidationResult(
                    is_valid=False,
                    error=ValidationError(
                        message="Missing Meta lead form id (source_id or workflow settings)"
                    ),
                )

            records = await self._fetch_leads(access_token, lead_form_id, limit=25)
            if not records:
                return ValidationResult(
                    is_valid=False,
                    error=ValidationError(
                        message="No leads found in Meta form. Add at least one lead before running campaign."
                    ),
                )

            rows = [self._lead_to_context(r) for r in records]
            headers = list({k for row in rows for k in row.keys()})
            data_rows = [[row.get(h, "") for h in headers] for row in rows]
            return self.validate_source_data(headers, data_rows)
        except httpx.HTTPStatusError as e:
            logger.error(f"Meta API validation failed: {e.response.status_code}")
            return ValidationResult(
                is_valid=False,
                error=ValidationError(
                    message=f"Failed to validate Meta source ({e.response.status_code})"
                ),
            )
        except Exception as e:
            logger.error(f"Meta source validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error=ValidationError(message="Failed to validate Meta source"),
            )

    async def sync_source_data(self, campaign_id: int) -> int:
        campaign = await db_client.get_campaign_by_id(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        workflow = await db_client.get_workflow_by_id(campaign.workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {campaign.workflow_id} not found")

        campaign_cfg = (workflow.workflow_configurations or {}).get(
            "campaign_integrations", {}
        )
        meta_cfg = campaign_cfg.get("meta_ads", {})
        access_token = (meta_cfg.get("access_token") or "").strip()
        lead_form_id = self._normalize_lead_form_id(
            campaign.source_id or meta_cfg.get("lead_form_id") or ""
        )
        if not access_token:
            raise ValueError(
                "Missing Meta access token in workflow campaign settings"
            )
        if not lead_form_id:
            raise ValueError(
                "Missing Meta lead form id (campaign source id or workflow settings)"
            )

        records = await self._fetch_leads(access_token, lead_form_id, limit=500)
        if not records:
            logger.warning(f"No leads found for campaign {campaign_id}")
            await db_client.update_campaign(
                campaign_id=campaign_id,
                total_rows=0,
                source_sync_status="completed",
            )
            return 0

        queued_runs = []
        for lead in records:
            context_vars = self._lead_to_context(lead)
            phone_number = context_vars.get("phone_number")
            if not phone_number:
                continue

            source_uuid = f"meta_lead_{lead.get('id')}"
            queued_runs.append(
                {
                    "campaign_id": campaign_id,
                    "source_uuid": source_uuid,
                    "context_variables": context_vars,
                    "state": "queued",
                }
            )

        if queued_runs:
            await db_client.bulk_create_queued_runs(queued_runs)

        await db_client.update_campaign(
            campaign_id=campaign_id,
            total_rows=len(queued_runs),
            source_sync_status="completed",
        )
        return len(queued_runs)

    async def _get_meta_config(self, workflow_id: int) -> dict[str, Any]:
        workflow = await db_client.get_workflow_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        return (workflow.workflow_configurations or {}).get(
            "campaign_integrations", {}
        ).get("meta_ads", {})

    async def _fetch_leads(
        self, access_token: str, lead_form_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        url = f"{self.graph_base}/{lead_form_id}/leads"
        params = {
            "fields": "id,created_time,field_data",
            "limit": min(limit, 500),
            "access_token": access_token,
        }

        all_rows: list[dict[str, Any]] = []
        next_url: Optional[str] = url
        next_params: Optional[dict[str, Any]] = params

        async with httpx.AsyncClient(timeout=30.0) as client:
            while next_url and len(all_rows) < limit:
                res = await client.get(next_url, params=next_params)
                res.raise_for_status()
                payload = res.json()
                rows = payload.get("data", [])
                all_rows.extend(rows)
                paging = payload.get("paging", {})
                next_url = paging.get("next")
                next_params = None  # `next` already includes params

        return all_rows[:limit]

    def _lead_to_context(self, lead: dict[str, Any]) -> dict[str, str]:
        context: dict[str, str] = {
            "meta_lead_id": str(lead.get("id", "")),
            "meta_created_time": str(lead.get("created_time", "")),
        }
        field_data = lead.get("field_data", []) or []
        for item in field_data:
            name = str(item.get("name", "")).strip().lower().replace(" ", "_")
            values = item.get("values", []) or []
            value = str(values[0]) if values else ""
            if name:
                context[name] = value

        # Normalize phone number aliases to the required key expected by campaigns
        for key in ("phone_number", "phone", "phone_no", "mobile", "mobile_number"):
            if context.get(key):
                context["phone_number"] = context[key]
                break

        return context

    def _normalize_lead_form_id(self, raw: str) -> str:
        raw = (raw or "").strip()
        if not raw:
            return ""
        # Accept plain form id or URLs containing the id.
        matched = re.search(r"(\d{8,})", raw)
        return matched.group(1) if matched else raw
