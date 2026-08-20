"""Vision AI analysis of disaster imagery using the Google Gemini API.

Bring your own key: create one free at https://aistudio.google.com/apikey and
put it in .env as GOOGLE_API_KEY. No third-party wrapper library is used - this
calls Google's official REST endpoint directly with `requests`.

Findings are decision-support signals only and must be verified by responders.
"""
import base64
import json
import re

import requests
from django.conf import settings

VALID_TYPES = {"damaged_building", "blocked_road", "service_disruption", "other"}

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={key}"
)

SYSTEM_MESSAGE = (
    "You are a cautious disaster-imagery analyst supporting emergency responders. "
    "You examine post-disaster drone, satellite or street-level images and identify "
    "POTENTIAL signs of damaged buildings, blocked roads and likely service/infrastructure "
    "disruptions. You never assert certainty. You always express findings as possibilities "
    "with calibrated confidence, because your output is a decision-support signal that a "
    "human responder must verify against official field assessment. "
    "Respond ONLY with strict JSON, no markdown, no commentary."
)


def _prompt(disaster):
    return (
        f"This image relates to a reported {disaster.disaster_type} incident named "
        f"'{disaster.name}' near {disaster.location}. "
        "Analyse the image and return JSON with EXACTLY this shape:\n"
        "{\n"
        '  "overall_confidence": <float 0-1>,\n'
        '  "summary": "<one sentence, neutral, operational>",\n'
        '  "findings": [\n'
        "    {\n"
        '      "finding_type": "damaged_building" | "blocked_road" | "service_disruption" | "other",\n'
        '      "label": "<short label>",\n'
        '      "location_hint": "<where in the image>",\n'
        '      "confidence": <float 0-1>,\n'
        '      "evidence": "<what visual cue supports this, e.g. collapsed roof, debris on road>"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "If you cannot identify anything reliably, return an empty findings list and a low "
        "overall_confidence. Do not invent damage that is not visible."
    )


def _extract_json(text):
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def _call_gemini(image_path, mime_type, disaster):
    with open(image_path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("utf-8")

    url = GEMINI_URL.format(model=settings.GOOGLE_MODEL, key=settings.GOOGLE_API_KEY)
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_MESSAGE}]},
        "contents": [{
            "role": "user",
            "parts": [
                {"text": _prompt(disaster)},
                {"inline_data": {"mime_type": mime_type, "data": b64}},
            ],
        }],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    resp = requests.post(url, json=body, timeout=60)
    if resp.status_code != 200:
        detail = ""
        try:
            detail = resp.json().get("error", {}).get("message", "")
        except Exception:  # noqa: BLE001
            detail = resp.text[:200]
        raise RuntimeError(f"Gemini API {resp.status_code}: {detail}")
    data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates.")
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts)


def analyze_image(image_path, mime_type, disaster):
    """Return a normalised dict of analysis results."""
    if not settings.GOOGLE_API_KEY:
        return {"status": "error",
                "error": "Google API key not configured. Add GOOGLE_API_KEY to .env.",
                "overall_confidence": 0.0, "summary": "", "findings": []}
    try:
        raw = _call_gemini(image_path, mime_type, disaster)
        data = _extract_json(raw)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"AI analysis unavailable: {exc}",
                "overall_confidence": 0.0, "summary": "", "findings": []}

    findings = []
    for item in data.get("findings", []) or []:
        ftype = item.get("finding_type", "other")
        if ftype not in VALID_TYPES:
            ftype = "other"
        try:
            conf = float(item.get("confidence", 0.0))
        except (TypeError, ValueError):
            conf = 0.0
        findings.append({
            "finding_type": ftype,
            "label": str(item.get("label", ""))[:200],
            "location_hint": str(item.get("location_hint", ""))[:250],
            "confidence": max(0.0, min(1.0, conf)),
            "evidence": str(item.get("evidence", ""))[:500],
        })

    try:
        overall = float(data.get("overall_confidence", 0.0))
    except (TypeError, ValueError):
        overall = 0.0

    return {
        "status": "completed",
        "error": "",
        "overall_confidence": max(0.0, min(1.0, overall)),
        "summary": str(data.get("summary", ""))[:500],
        "findings": findings,
    }
