from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


# Sarvam published pricing:
# - Bulbul v3: INR 30 / 10,000 characters
# - Saarika v2.5 STT: INR 30 / hour
SARVAM_BULBUL_V3_INR_PER_10K_CHARS = Decimal("30")
SARVAM_SAARIKA_INR_PER_HOUR = Decimal("30")

# OpenRouter model pricing assumed identical to OpenAI model card pricing for gpt-4.1-mini.
GPT_41_MINI_USD_PER_1M_PROMPT = Decimal("0.40")
GPT_41_MINI_USD_PER_1M_COMPLETION = Decimal("1.60")

# Static FX fallback for reporting INR totals from USD components.
USD_TO_INR = Decimal("83")


@dataclass
class INRPriceBreakdown:
    llm_inr: float
    tts_inr: float
    stt_inr: float
    telephony_inr: float
    total_inr: float
    credits_used: float
    duration_minutes: float


def calculate_inr_pricing(
    usage_info: dict[str, Any] | None,
    cost_info: dict[str, Any] | None,
) -> INRPriceBreakdown:
    usage_info = usage_info or {}
    cost_info = cost_info or {}

    llm_inr = _llm_inr(usage_info.get("llm", {}))
    tts_inr = _tts_inr(usage_info.get("tts", {}))
    stt_inr = _stt_inr(usage_info.get("stt", {}))
    telephony_inr = _telephony_inr(cost_info)

    total = llm_inr + tts_inr + stt_inr + telephony_inr
    seconds = _to_decimal(usage_info.get("call_duration_seconds", 0))

    return INRPriceBreakdown(
        llm_inr=float(llm_inr),
        tts_inr=float(tts_inr),
        stt_inr=float(stt_inr),
        telephony_inr=float(telephony_inr),
        total_inr=float(total),
        credits_used=float(total),
        duration_minutes=float(seconds / Decimal("60")),
    )


def _llm_inr(llm_usage: dict[str, Any]) -> Decimal:
    total_usd = Decimal("0")
    for key, usage in (llm_usage or {}).items():
        if not isinstance(usage, dict):
            continue
        model = _extract_model_name(str(key)).lower()
        if model not in {"gpt-4.1-mini", "openai/gpt-4.1-mini"}:
            continue

        prompt_tokens = _to_decimal(usage.get("prompt_tokens", 0))
        completion_tokens = _to_decimal(usage.get("completion_tokens", 0))
        prompt_cost = (prompt_tokens / Decimal("1000000")) * GPT_41_MINI_USD_PER_1M_PROMPT
        completion_cost = (completion_tokens / Decimal("1000000")) * GPT_41_MINI_USD_PER_1M_COMPLETION
        total_usd += prompt_cost + completion_cost
    return total_usd * USD_TO_INR


def _tts_inr(tts_usage: dict[str, Any]) -> Decimal:
    total = Decimal("0")
    for key, char_count in (tts_usage or {}).items():
        model = _extract_model_name(str(key)).lower()
        if model != "bulbul:v3":
            continue
        chars = _to_decimal(char_count)
        total += (chars / Decimal("10000")) * SARVAM_BULBUL_V3_INR_PER_10K_CHARS
    return total


def _stt_inr(stt_usage: dict[str, Any]) -> Decimal:
    total = Decimal("0")
    for key, seconds in (stt_usage or {}).items():
        model = _extract_model_name(str(key)).lower()
        if model not in {"saarika:v2.5", "saarika-v2.5"}:
            continue
        secs = _to_decimal(seconds)
        total += (secs / Decimal("3600")) * SARVAM_SAARIKA_INR_PER_HOUR
    return total


def _telephony_inr(cost_info: dict[str, Any]) -> Decimal:
    # Telephony cost is captured in USD by provider APIs (twilio_call/telephony_call).
    telephony_usd = _to_decimal(
        cost_info.get("twilio_call")
        or cost_info.get("telephony_call")
        or cost_info.get("vonage_call")
        or 0
    )
    return telephony_usd * USD_TO_INR


def _extract_model_name(key: str) -> str:
    if "|||" not in key:
        return key
    return key.split("|||", 1)[1]


def _to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")
