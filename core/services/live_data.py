"""Live external data sources used by RESQAI.

The live feeds are public/free sources. No demo or fabricated events are
inserted into the live panels. When a feed returns zero matching events, the
frontend can safely report that no matching event was detected.
"""
import csv
import io
import time
from datetime import datetime, timezone

import requests
from django.conf import settings

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"

# India bounding box used to keep live feeds focused on India only.
INDIA_BBOX = {"min_lat": 6.0, "max_lat": 37.5, "min_lng": 68.0, "max_lng": 97.5}
ONLY_INDIA = True  # set False to show the whole world again

_CACHE = {}
_CACHE_TTL = {"usgs": 60, "fires": 300}


def _in_india(lat, lng):
    if lat is None or lng is None:
        return False
    return (INDIA_BBOX["min_lat"] <= lat <= INDIA_BBOX["max_lat"]
            and INDIA_BBOX["min_lng"] <= lng <= INDIA_BBOX["max_lng"])

def _age_label(seconds):
    if seconds < 120:
        return "LIVE"
    if seconds < 900:
        return "NEAR REAL-TIME"
    if seconds < 3600:
        return "RECENT"
    return "STALE"


def _cached(key):
    entry = _CACHE.get(key)
    if entry and (time.time() - entry["fetched_at"]) < _CACHE_TTL[key]:
        return entry
    return None


def get_earthquakes(min_magnitude=0.0):
    cached = _cached("usgs")
    if cached:
        payload = cached
    else:
        try:
            resp = requests.get(USGS_URL, timeout=12)
            resp.raise_for_status()
            data = resp.json()
            events = []
            for feat in data.get("features", []):
                props = feat.get("properties", {})
                geom = feat.get("geometry", {}) or {}
                coords = geom.get("coordinates", [None, None, None])
                lng = coords[0] if len(coords) > 0 else None
                lat = coords[1] if len(coords) > 1 else None
                place = props.get("place") or ""
                # India only: must be inside the India region AND labelled India
                # (blocks Afghanistan/Pakistan via label, and "Indian Springs, USA" via box).
                if ONLY_INDIA and not (_in_india(lat, lng) and "india" in place.lower()):
                    continue
                events.append({
                    "id": feat.get("id"),
                    "magnitude": props.get("mag"),
                    "depth_km": coords[2] if len(coords) > 2 else None,
                    "location": props.get("place"),
                    "longitude": lng,
                    "latitude": lat,
                    "time": props.get("time"),
                    "time_iso": datetime.fromtimestamp(
                        props.get("time", 0) / 1000, tz=timezone.utc
                    ).isoformat() if props.get("time") else None,
                    "url": props.get("url"),
                    "source": "USGS",
                })
            payload = {
                "fetched_at": time.time(),
                "status": "connected",
                "events": events,
            }
            _CACHE["usgs"] = payload
        except Exception as exc:  # noqa: BLE001
            return {
                "source": "USGS",
                "status": "unavailable",
                "connection": "UNAVAILABLE",
                "message": "Live earthquake data temporarily unavailable.",
                "detail": str(exc),
                "events": [],
                "last_updated": None,
                "data_age_seconds": None,
            }

    age = int(time.time() - payload["fetched_at"])
    events = payload["events"]
    if min_magnitude:
        events = [e for e in events if (e["magnitude"] or 0) >= min_magnitude]
    return {
        "source": "USGS",
        "status": "connected",
        "connection": _age_label(age),
        "count": len(events),
        "events": events,
        "last_updated": datetime.fromtimestamp(
            payload["fetched_at"], tz=timezone.utc).isoformat(),
        "data_age_seconds": age,
    }

EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=200"
GDACS_RSS = "https://www.gdacs.org/xml/rss.xml"
GDACS_NS = {
    "gdacs": "http://www.gdacs.org",
    "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
    "georss": "http://www.georss.org/georss",
}
GDACS_TYPES = {
    "EQ": "Earthquake", "TC": "Cyclone", "FL": "Flood",
    "DR": "Drought", "WF": "Wildfire", "VO": "Volcano", "TS": "Tsunami",
}


def _gdacs_coords(item):
    lat = item.findtext("geo:lat", default="", namespaces=GDACS_NS)
    lon = item.findtext("geo:long", default="", namespaces=GDACS_NS)
    if not lat:
        lat = item.findtext("gdacs:latitude", default="", namespaces=GDACS_NS)
        lon = item.findtext("gdacs:longitude", default="", namespaces=GDACS_NS)
    if not lat:
        pt = item.findtext("georss:point", default="", namespaces=GDACS_NS)
        if pt and len(pt.split()) == 2:
            lat, lon = pt.split()
    try:
        return float(lat), float(lon)
    except (TypeError, ValueError):
        return None, None


EONET_WILDFIRE_URL = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&category=wildfires&limit=500"


def _eonet_fire_detections():
    """Fallback free NASA EONET wildfire feed, filtered to India."""
    resp = requests.get(EONET_WILDFIRE_URL, timeout=15, headers={"User-Agent": "RESQAI/1.0"})
    resp.raise_for_status()
    data = resp.json()
    detections = []
    for event in data.get("events", []):
        for geometry in event.get("geometry", []) or []:
            coords = geometry.get("coordinates") or []
            if geometry.get("type") == "Point" and len(coords) >= 2:
                lon, lat = coords[0], coords[1]
                if _in_india(lat, lon):
                    detections.append({
                        "id": event.get("id"),
                        "latitude": lat,
                        "longitude": lon,
                        "title": event.get("title") or "Wildfire alert",
                        "category": "Wildfire",
                        "confidence": "NASA EONET",
                        "acq_date": geometry.get("date"),
                        "satellite": "NASA EONET",
                        "source": "NASA EONET",
                    })
    return detections


def get_fires(map_key=None):
    """Return current India wildfire alerts from free public feeds.

    GDACS is the primary source. NASA EONET is used as a no-key fallback so a
    temporary GDACS outage does not make the fire panel unusable.
    """
    cached = _cached("fires")
    if cached:
        payload = cached
    else:
        detections = None
        source = None
        errors = []

        # Primary: GDACS public GeoRSS feed.
        try:
            import xml.etree.ElementTree as ET
            resp = requests.get(
                GDACS_RSS, timeout=15,
                headers={"User-Agent": "RESQAI/1.0"},
            )
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            detections = []
            for item in root.findall(".//item"):
                event_type = (
                    item.findtext("gdacs:eventtype", default="", namespaces=GDACS_NS)
                    or ""
                ).strip().upper()
                if event_type != "WF":
                    continue
                country = item.findtext("gdacs:country", default="", namespaces=GDACS_NS) or ""
                title = item.findtext("title", default="") or ""
                lat, lon = _gdacs_coords(item)
                if "india" not in country.lower() and "india" not in title.lower():
                    continue
                if not _in_india(lat, lon):
                    continue
                alert = item.findtext("gdacs:alertlevel", default="", namespaces=GDACS_NS) or "Info"
                pub_date = item.findtext("pubDate", default="") or ""
                detections.append({
                    "latitude": lat,
                    "longitude": lon,
                    "title": title,
                    "category": "Wildfire",
                    "confidence": alert,
                    "acq_date": pub_date,
                    "satellite": "GDACS",
                    "source": "GDACS",
                })
            source = "GDACS (India wildfires)"
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))

        # Fallback: NASA EONET, also public and no API key required.
        if detections is None:
            try:
                detections = _eonet_fire_detections()
                source = "NASA EONET (India wildfires)"
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))

        if detections is None:
            return {
                "source": "GDACS / NASA EONET (India wildfires)",
                "status": "unavailable",
                "connection": "UNAVAILABLE",
                "message": "Live fire sources are temporarily unavailable. Fire status cannot be confirmed right now.",
                "detail": " | ".join(errors[-2:]),
                "detections": [],
                "last_updated": None,
                "data_age_seconds": None,
            }

        payload = {
            "fetched_at": time.time(),
            "detections": detections,
            "source": source,
        }
        _CACHE["fires"] = payload

    age = int(time.time() - payload["fetched_at"])
    return {
        "source": payload.get("source", "GDACS / NASA EONET (India wildfires)"),
        "status": "connected",
        "connection": _age_label(age),
        "count": len(payload["detections"]),
        "detections": payload["detections"],
        "last_updated": datetime.fromtimestamp(payload["fetched_at"], tz=timezone.utc).isoformat(),
        "data_age_seconds": age,
    }

