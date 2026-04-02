"""
Plivo implementation of the TelephonyProvider interface.
"""

import json
import random
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import aiohttp
from fastapi import HTTPException
from loguru import logger

from api.enums import WorkflowRunMode
from api.services.telephony.base import (
    CallInitiationResult,
    NormalizedInboundData,
    TelephonyProvider,
)
from api.utils.common import get_backend_endpoints

if TYPE_CHECKING:
    from fastapi import WebSocket


class PlivoProvider(TelephonyProvider):
    """
    Plivo implementation of TelephonyProvider.
    """

    PROVIDER_NAME = WorkflowRunMode.PLIVO.value
    WEBHOOK_ENDPOINT = "plivo-xml"

    def __init__(self, config: Dict[str, Any]):
        self.auth_id = config.get("auth_id")
        self.auth_token = config.get("auth_token")
        self.from_numbers = config.get("from_numbers", [])

        if isinstance(self.from_numbers, str):
            self.from_numbers = [self.from_numbers]

        self.base_url = f"https://api.plivo.com/v1/Account/{self.auth_id}"

    async def initiate_call(
        self,
        to_number: str,
        webhook_url: str,
        workflow_run_id: Optional[int] = None,
        from_number: Optional[str] = None,
        **kwargs: Any,
    ) -> CallInitiationResult:
        if not self.validate_config():
            raise ValueError("Plivo provider not properly configured")

        endpoint = f"{self.base_url}/Call/"

        if from_number is None:
            from_number = random.choice(self.from_numbers)
        logger.info(f"Selected Plivo phone number {from_number} for outbound call")

        to_number_clean = to_number.lstrip("+")
        from_number_clean = from_number.lstrip("+")

        data = {
            "from": from_number_clean,
            "to": to_number_clean,
            "answer_url": webhook_url,
            "answer_method": "POST",
        }

        if workflow_run_id:
            backend_endpoint, _ = await get_backend_endpoints()
            hangup_url = (
                f"{backend_endpoint}/api/v1/telephony/vobiz/hangup-callback/{workflow_run_id}"
            )
            ring_url = (
                f"{backend_endpoint}/api/v1/telephony/vobiz/ring-callback/{workflow_run_id}"
            )
            data.update(
                {
                    "hangup_url": hangup_url,
                    "hangup_method": "POST",
                    "ring_url": ring_url,
                    "ring_method": "POST",
                }
            )

        data.update(kwargs)

        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(self.auth_id, self.auth_token)
            async with session.post(endpoint, json=data, auth=auth) as response:
                if response.status != 201:
                    error_data = await response.text()
                    logger.error(f"Plivo API error: {error_data}")
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Failed to initiate Plivo call: {error_data}",
                    )

                response_data = await response.json()
                logger.info(f"Plivo API response: {response_data}")

                call_id = response_data.get("request_uuid")
                if not call_id:
                    logger.error(
                        f"No request_uuid found in Plivo response. Keys: {list(response_data.keys())}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail="Plivo API response missing request_uuid",
                    )

                return CallInitiationResult(
                    call_id=call_id,
                    status="queued",
                    provider_metadata={"call_id": call_id},
                    raw_response=response_data,
                )

    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        if not self.validate_config():
            raise ValueError("Plivo provider not properly configured")

        endpoint = f"{self.base_url}/Call/{call_id}/"
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(self.auth_id, self.auth_token)
            async with session.get(endpoint, auth=auth) as response:
                if response.status != 200:
                    error_data = await response.text()
                    logger.error(f"Failed to get Plivo call status: {error_data}")
                    raise Exception(f"Failed to get call status: {error_data}")

                return await response.json()

    async def get_available_phone_numbers(self) -> List[str]:
        return self.from_numbers

    def validate_config(self) -> bool:
        return bool(self.auth_id and self.auth_token and self.from_numbers)

    async def verify_webhook_signature(
        self, url: str, params: Dict[str, Any], signature: str
    ) -> bool:
        # Plivo signature verification can be added when strict verification is enabled.
        return bool(signature)

    async def get_webhook_response(
        self, workflow_id: int, user_id: int, workflow_run_id: int
    ) -> str:
        _, wss_backend_endpoint = await get_backend_endpoints()
        plivo_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Stream bidirectional="true" keepCallAlive="true" contentType="audio/x-mulaw;rate=8000">{wss_backend_endpoint}/api/v1/telephony/ws/{workflow_id}/{user_id}/{workflow_run_id}</Stream>
</Response>"""
        return plivo_xml

    async def get_call_cost(self, call_id: str) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/Call/{call_id}/"
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.auth_id, self.auth_token)
                async with session.get(endpoint, auth=auth) as response:
                    if response.status != 200:
                        error_data = await response.text()
                        logger.error(f"Failed to get Plivo call cost: {error_data}")
                        return {
                            "cost_usd": 0.0,
                            "duration": 0,
                            "status": "error",
                            "error": str(error_data),
                        }

                    call_data = await response.json()
                    total_cost_str = call_data.get("total_amount", "0")
                    cost_usd = float(total_cost_str) if total_cost_str else 0.0
                    duration = int(call_data.get("bill_duration", 0))

                    return {
                        "cost_usd": cost_usd,
                        "duration": duration,
                        "status": call_data.get("call_status", "unknown"),
                        "price_unit": "USD",
                        "raw_response": call_data,
                    }
        except Exception as e:
            logger.error(f"Exception fetching Plivo call cost: {e}")
            return {"cost_usd": 0.0, "duration": 0, "status": "error", "error": str(e)}

    def parse_status_callback(self, data: Dict[str, Any]) -> Dict[str, Any]:
        status_map = {
            "ringing": "ringing",
            "in-progress": "in-progress",
            "completed": "completed",
            "busy": "busy",
            "no-answer": "no-answer",
            "failed": "failed",
            "canceled": "canceled",
        }
        raw_status = data.get("CallStatus", data.get("call_status", ""))
        return {
            "call_id": data.get("CallUUID", data.get("call_uuid", "")),
            "status": status_map.get(raw_status.lower(), raw_status.lower()),
            "from_number": data.get("From", data.get("from")),
            "to_number": data.get("To", data.get("to")),
            "direction": data.get("Direction", data.get("direction")),
            "duration": data.get("Duration", data.get("duration")),
            "extra": data,
        }

    async def handle_websocket(
        self,
        websocket: "WebSocket",
        workflow_id: int,
        user_id: int,
        workflow_run_id: int,
    ) -> None:
        from api.services.pipecat.run_pipeline import run_pipeline_vobiz

        first_msg = await websocket.receive_text()
        start_msg = json.loads(first_msg)
        logger.debug(f"Received Plivo first message: {start_msg}")

        if start_msg.get("event") != "start":
            logger.error(f"Expected 'start' event, got: {start_msg.get('event')}")
            await websocket.close(code=4400, reason="Expected start event")
            return

        start_data = start_msg.get("start", {})
        stream_id = start_data.get("streamId") or start_data.get("stream_id")
        call_id = (
            start_data.get("callId")
            or start_data.get("call_id")
            or start_data.get("callUUID")
            or start_data.get("call_uuid")
        )

        if not stream_id or not call_id:
            logger.error(f"Missing stream/call identifiers in Plivo start event: {start_data}")
            await websocket.close(code=4400, reason="Missing stream/call identifiers")
            return

        await run_pipeline_vobiz(
            websocket, stream_id, call_id, workflow_id, workflow_run_id, user_id
        )

    @classmethod
    def can_handle_webhook(
        cls, webhook_data: Dict[str, Any], headers: Dict[str, str]
    ) -> bool:
        return "x-plivo-signature-v2" in headers or "x-plivo-signature-v3" in headers

    @staticmethod
    def parse_inbound_webhook(webhook_data: Dict[str, Any]) -> NormalizedInboundData:
        return NormalizedInboundData(
            provider=PlivoProvider.PROVIDER_NAME,
            call_id=webhook_data.get("CallUUID", webhook_data.get("call_uuid", "")),
            from_number=PlivoProvider.normalize_phone_number(
                webhook_data.get("From", webhook_data.get("from", ""))
            ),
            to_number=PlivoProvider.normalize_phone_number(
                webhook_data.get("To", webhook_data.get("to", ""))
            ),
            direction=webhook_data.get("Direction", webhook_data.get("direction", "")),
            call_status=webhook_data.get(
                "CallStatus", webhook_data.get("call_status", "")
            ),
            account_id=webhook_data.get("AuthID", webhook_data.get("auth_id")),
            raw_data=webhook_data,
        )

    @staticmethod
    def validate_account_id(config_data: dict, webhook_account_id: str) -> bool:
        if not webhook_account_id:
            return False
        return config_data.get("auth_id") == webhook_account_id

    @staticmethod
    def normalize_phone_number(phone_number: str) -> str:
        if not phone_number:
            return ""
        clean_number = phone_number.lstrip("+")
        if clean_number.startswith("1") and len(clean_number) == 11:
            return f"+{clean_number}"
        if len(clean_number) == 10:
            return f"+1{clean_number}"
        if len(clean_number) > 10:
            return f"+{clean_number}"
        return phone_number

    async def verify_inbound_signature(
        self, url: str, webhook_data: Dict[str, Any], signature: str
    ) -> bool:
        return await self.verify_webhook_signature(url, webhook_data, signature)

    @staticmethod
    async def generate_inbound_response(
        websocket_url: str, workflow_run_id: int = None
    ) -> tuple:
        from fastapi import Response

        plivo_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Stream bidirectional="true" keepCallAlive="true" contentType="audio/x-mulaw;rate=8000">{websocket_url}</Stream>
</Response>"""
        return Response(content=plivo_xml, media_type="application/xml")

    @staticmethod
    def generate_error_response(error_type: str, message: str) -> tuple:
        from fastapi import Response

        plivo_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak voice="WOMAN">Sorry, there was an error processing your call. {message}</Speak>
    <Hangup/>
</Response>"""
        return Response(content=plivo_xml, media_type="application/xml")

    @staticmethod
    def generate_validation_error_response(error_type) -> tuple:
        from fastapi import Response

        from api.errors.telephony_errors import TELEPHONY_ERROR_MESSAGES, TelephonyError

        message = TELEPHONY_ERROR_MESSAGES.get(
            error_type, TELEPHONY_ERROR_MESSAGES[TelephonyError.GENERAL_AUTH_FAILED]
        )
        plivo_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak voice="WOMAN">{message}</Speak>
    <Hangup/>
</Response>"""
        return Response(content=plivo_xml, media_type="application/xml")

    async def transfer_call(
        self,
        destination: str,
        transfer_id: str,
        conference_name: str,
        timeout: int = 30,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        raise NotImplementedError("Plivo provider does not support call transfers")

    def supports_transfers(self) -> bool:
        return False
