import re
from datetime import UTC, datetime
from typing import Any, Optional

import httpx
from loguru import logger

from api.db import db_client
from api.services.campaign.google_auth import resolve_google_access_token
from api.services.integrations.nango import NangoService
from api.services.pricing.inr_pricing import calculate_inr_pricing
from api.utils.transcript import generate_transcript_text


class CampaignOutputSyncService:
    """Sync completed campaign call outputs to external destinations."""

    sheets_api_base = "https://sheets.googleapis.com/v4/spreadsheets"

    def __init__(self):
        self.nango_service = NangoService()

    async def sync_workflow_run_output(self, workflow_run_id: int) -> None:
        workflow_run, organization_id = await db_client.get_workflow_run_with_context(
            workflow_run_id
        )
        if not workflow_run or not workflow_run.campaign_id:
            return

        workflow = workflow_run.workflow
        if not workflow:
            return
        organization_id = organization_id or workflow.organization_id
        if not organization_id:
            return

        campaign = await db_client.get_campaign_by_id(workflow_run.campaign_id)
        campaign_source_auth = (
            (campaign.orchestrator_metadata or {}).get("source_auth", {})
            if campaign
            else {}
        )

        campaign_cfg = (workflow.workflow_configurations or {}).get(
            "campaign_integrations", {}
        )
        google_cfg = campaign_cfg.get("google_sheets", {})
        output_sheet_url = (
            campaign_source_auth.get("output_sheet_url")
            or google_cfg.get("output_sheet_url")
            or ""
        ).strip()
        if not output_sheet_url:
            return

        access_token = await self._get_google_access_token(
            organization_id=organization_id,
            source_auth=campaign_source_auth
            if campaign_source_auth
            else {"access_token": google_cfg.get("access_token")},
        )
        if not access_token:
            logger.warning(
                f"workflow_run_id={workflow_run_id}: Missing Google access token for output sync"
            )
            return

        try:
            sheet_id = self._extract_sheet_id(output_sheet_url)
            sheet_name = await self._get_first_sheet_name(sheet_id, access_token)
            row = self._build_output_row(workflow_run)
            await self._append_row(sheet_id, sheet_name, row, access_token)
            logger.info(
                f"workflow_run_id={workflow_run_id}: Synced campaign output row to Google Sheet"
            )
        except Exception as e:
            logger.error(
                f"workflow_run_id={workflow_run_id}: Failed to sync campaign output to Google Sheet: {e}"
            )

    async def _get_google_access_token(
        self, organization_id: int, source_auth: Optional[dict]
    ) -> Optional[str]:
        token = await resolve_google_access_token(source_auth)
        if token:
            return token

        integrations = await db_client.get_integrations_by_organization_id(organization_id)
        integration = next(
            (
                i
                for i in integrations
                if i.provider == "google-sheet" and i.is_active and i.integration_id
            ),
            None,
        )
        if not integration:
            return None

        token_data = await self.nango_service.get_access_token(
            connection_id=integration.integration_id,
            provider_config_key="google-sheet",
        )
        return token_data.get("credentials", {}).get("access_token")

    async def _get_first_sheet_name(self, sheet_id: str, access_token: str) -> str:
        url = f"{self.sheets_api_base}/{sheet_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            payload = response.json()
            sheets = payload.get("sheets", [])
            if not sheets:
                raise ValueError("No sheets found in output spreadsheet")
            return sheets[0]["properties"]["title"]

    async def _append_row(
        self, sheet_id: str, sheet_name: str, row: list[Any], access_token: str
    ) -> None:
        safe_sheet = sheet_name.replace("'", "''")
        url = f"{self.sheets_api_base}/{sheet_id}/values/{safe_sheet}!A:Z:append"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        params = {"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}
        payload = {"values": [row]}

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, headers=headers, params=params, json=payload)
            response.raise_for_status()

    def _extract_sheet_id(self, sheet_url: str) -> str:
        pattern = r"/spreadsheets/d/([a-zA-Z0-9-_]+)"
        match = re.search(pattern, sheet_url)
        if not match:
            raise ValueError(f"Invalid Google Sheet URL: {sheet_url}")
        return match.group(1)

    def _build_output_row(self, workflow_run) -> list[Any]:
        logs = workflow_run.logs or {}
        callback_logs = logs.get("telephony_status_callbacks", [])
        last_status = callback_logs[-1].get("status", "") if callback_logs else ""

        transcript = generate_transcript_text(
            logs.get("realtime_feedback_events", []) or []
        ).strip()

        pricing = calculate_inr_pricing(workflow_run.usage_info, workflow_run.cost_info)
        gathered = workflow_run.gathered_context or {}
        initial = workflow_run.initial_context or {}

        return [
            datetime.now(UTC).isoformat(),
            workflow_run.id,
            workflow_run.campaign_id,
            workflow_run.workflow_id,
            initial.get("phone_number") or "",
            last_status,
            gathered.get("mapped_call_disposition") or "",
            int(round((workflow_run.usage_info or {}).get("call_duration_seconds", 0))),
            transcript,
            round(pricing.total_inr, 2),
            round(pricing.credits_used, 2),
        ]


campaign_output_sync_service = CampaignOutputSyncService()
