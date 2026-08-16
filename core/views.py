import math
import requests

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    Disaster, EvidenceEvent, Finding, ImageAnalysis, PriorityZone,
    Report, ResponseAssignment, RoutePlan, Verification,
)
from .serializers import (
    DisasterSerializer, EvidenceEventSerializer, FindingSerializer,
    ImageAnalysisSerializer, PriorityZoneSerializer, RegisterSerializer,
    ReportSerializer, ResponseAssignmentSerializer, RoutePlanSerializer,
    UserSerializer, VerificationSerializer,
)
from .services import ai_analysis, live_data
from .services.priority import compute_priority


def log_event(disaster, action, actor="", source="", evidence_ref=""):
    EvidenceEvent.objects.create(
        disaster=disaster, action=action, actor=actor,
        source=source, evidence_ref=evidence_ref,
    )


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)), 2)


# --------------------------- Auth ---------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {"token": token.key, "user": UserSerializer(user).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password") or ""
    user = authenticate(username=email, password=password)
    if user is None:
        candidate = User.objects.filter(email__iexact=email).first()
        if candidate:
            user = authenticate(username=candidate.username, password=password)
    if user is None:
        return Response({"detail": "Invalid email or password."},
                        status=status.HTTP_401_UNAUTHORIZED)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": UserSerializer(user).data})


@api_view(["POST"])
def logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response({"detail": "Logged out."})


@api_view(["GET"])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(["GET"])
def responders(request):
    users = User.objects.all()
    return Response(UserSerializer(users, many=True).data)


# --------------------------- Dashboard ---------------------------
@api_view(["GET"])
def dashboard_stats(request):
    active = Disaster.objects.filter(status="active").count()
    critical_zones = PriorityZone.objects.filter(priority_score__gte=75).count()
    pending_verification = Finding.objects.filter(verification_status="unverified").count()
    blocked_routes = Finding.objects.filter(finding_type="blocked_road").count()
    affected = sum(d.affected_population or 0 for d in Disaster.objects.all())
    return Response({
        "active_incidents": active,
        "critical_zones": critical_zones,
        "pending_verification": pending_verification,
        "blocked_routes": blocked_routes,
        "people_affected": affected,
        "total_incidents": Disaster.objects.count(),
        "priority_zones": PriorityZoneSerializer(
            PriorityZone.objects.all()[:5], many=True).data,
        # Full incident history, newest first via Disaster.Meta ordering.
        "recent_incidents": DisasterSerializer(
            Disaster.objects.all(), many=True).data,
        "recent_evidence": EvidenceEventSerializer(
            EvidenceEvent.objects.all()[:6], many=True).data,
    })


# --------------------------- Disasters ---------------------------
@api_view(["GET", "POST"])
def disasters(request):
    if request.method == "GET":
        qs = Disaster.objects.all()
        dtype = request.query_params.get("type")
        severity = request.query_params.get("severity")
        dstatus = request.query_params.get("status")
        if dtype:
            qs = qs.filter(disaster_type=dtype)
        if severity:
            qs = qs.filter(severity=severity)
        if dstatus:
            qs = qs.filter(status=dstatus)
        return Response(DisasterSerializer(qs, many=True).data)

    serializer = DisasterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    disaster = serializer.save(created_by=request.user)
    log_event(disaster, f"Incident '{disaster.name}' created",
              actor=request.user.username, source="Operator",
              evidence_ref=disaster.incident_code)
    return Response(DisasterSerializer(disaster).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def disaster_detail(request, pk):
    try:
        disaster = Disaster.objects.get(pk=pk)
    except Disaster.DoesNotExist:
        return Response({"detail": "Incident not found."}, status=status.HTTP_404_NOT_FOUND)
    data = DisasterSerializer(disaster).data
    data["findings"] = FindingSerializer(disaster.findings.all(), many=True).data
    data["analyses"] = ImageAnalysisSerializer(disaster.analyses.all(), many=True).data
    data["priority_zones"] = PriorityZoneSerializer(disaster.priority_zones.all(), many=True).data
    data["reports"] = ReportSerializer(disaster.reports.all(), many=True).data
    data["assignments"] = ResponseAssignmentSerializer(disaster.assignments.all(), many=True).data
    data["routes"] = RoutePlanSerializer(disaster.routes.all(), many=True).data
    data["timeline"] = EvidenceEventSerializer(disaster.timeline.all(), many=True).data
    return Response(data)


@api_view(["GET"])
def disaster_timeline(request, pk):
    try:
        disaster = Disaster.objects.get(pk=pk)
    except Disaster.DoesNotExist:
        return Response({"detail": "Incident not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(EvidenceEventSerializer(disaster.timeline.all(), many=True).data)


# --------------------------- Live situation ---------------------------
@api_view(["GET"])
def live_situation(request):
    qs = Disaster.objects.all()
    dtype = request.query_params.get("type")
    severity = request.query_params.get("severity")
    dstatus = request.query_params.get("status")
    if dtype:
        qs = qs.filter(disaster_type=dtype)
    if severity:
        qs = qs.filter(severity=severity)
    if dstatus:
        qs = qs.filter(status=dstatus)
    return Response(DisasterSerializer(qs, many=True).data)


# --------------------------- Image analysis ---------------------------
ALLOWED_MIME = {"image/jpeg": "image/jpeg", "image/jpg": "image/jpeg",
                "image/png": "image/png", "image/webp": "image/webp"}


@api_view(["GET"])
def image_analyses(request):
    qs = ImageAnalysis.objects.all()
    disaster_id = request.query_params.get("disaster")
    if disaster_id:
        qs = qs.filter(disaster_id=disaster_id)
    return Response(ImageAnalysisSerializer(qs, many=True).data)


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def analyze_image(request):
    disaster_id = request.data.get("disaster_id") or request.data.get("disaster")
    image = request.FILES.get("image")
    if not disaster_id or not image:
        return Response({"detail": "disaster_id and image are required."},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        disaster = Disaster.objects.get(pk=disaster_id)
    except Disaster.DoesNotExist:
        return Response({"detail": "Incident not found."}, status=status.HTTP_404_NOT_FOUND)

    mime = ALLOWED_MIME.get((image.content_type or "").lower())
    if not mime:
        return Response({"detail": "Unsupported file type. Use JPG, PNG or WEBP."},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    if image.size > 10 * 1024 * 1024:
        return Response({"detail": "Image exceeds 10 MB limit."},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    analysis = ImageAnalysis.objects.create(
        disaster=disaster, image=image, created_by=request.user,
        model_used=f"{settings.AI_MODEL_PROVIDER}/{settings.AI_MODEL_NAME}",
    )
    log_event(disaster, "Image received for analysis", actor=request.user.username,
              source="Image Analysis", evidence_ref=analysis.analysis_code)

    result = ai_analysis.analyze_image(analysis.image.path, mime, disaster)
    analysis.overall_confidence = result.get("overall_confidence", 0.0)
    analysis.summary = result.get("summary", "")
    analysis.status = result.get("status", "completed")
    analysis.error = result.get("error", "")
    analysis.save()

    for f in result.get("findings", []):
        Finding.objects.create(
            analysis=analysis, disaster=disaster,
            finding_type=f["finding_type"], label=f["label"],
            location_hint=f["location_hint"], confidence=f["confidence"],
            evidence=f["evidence"],
        )
    if analysis.status == "completed":
        log_event(disaster,
                  f"AI analysis completed ({len(result.get('findings', []))} findings)",
                  actor="AI (decision-support)", source=analysis.model_used,
                  evidence_ref=analysis.analysis_code)

    return Response(ImageAnalysisSerializer(analysis).data, status=status.HTTP_201_CREATED)


# --------------------------- Verification ---------------------------
@api_view(["GET"])
def verification_queue(request):
    qs = Finding.objects.filter(verification_status="unverified")
    return Response(FindingSerializer(qs, many=True).data)


@api_view(["POST"])
def verify_finding(request, pk):
    try:
        finding = Finding.objects.get(pk=pk)
    except Finding.DoesNotExist:
        return Response({"detail": "Finding not found."}, status=status.HTTP_404_NOT_FOUND)
    action = request.data.get("action")
    if action not in {"confirm", "correct", "reject"}:
        return Response({"detail": "action must be confirm, correct or reject."},
                        status=status.HTTP_400_BAD_REQUEST)

    verification = Verification.objects.create(
        finding=finding, action=action,
        correct_classification=request.data.get("correct_classification", ""),
        reason=request.data.get("reason", ""),
        notes=request.data.get("notes", ""),
        verified_by=request.user,
    )
    if action == "confirm":
        finding.verification_status = "confirmed"
    elif action == "reject":
        finding.verification_status = "rejected"
    elif action == "correct":
        finding.verification_status = "corrected"
        if request.data.get("correct_classification"):
            finding.finding_type = request.data["correct_classification"]
    finding.save()

    log_event(finding.disaster,
              f"Finding {finding.finding_code} {finding.verification_status} by responder",
              actor=request.user.username, source="Verification",
              evidence_ref=finding.finding_code)
    return Response({
        "finding": FindingSerializer(finding).data,
        "verification": VerificationSerializer(verification).data,
    }, status=status.HTTP_201_CREATED)


# --------------------------- Priority zones ---------------------------
@api_view(["GET", "POST"])
def priority_zones(request):
    if request.method == "GET":
        qs = PriorityZone.objects.all()
        disaster_id = request.query_params.get("disaster")
        if disaster_id:
            qs = qs.filter(disaster_id=disaster_id)
        return Response(PriorityZoneSerializer(qs, many=True).data)

    disaster_id = request.data.get("disaster")
    try:
        disaster = Disaster.objects.get(pk=disaster_id)
    except Disaster.DoesNotExist:
        return Response({"detail": "Incident not found."}, status=status.HTTP_404_NOT_FOUND)

    def num(key, default=0.0):
        try:
            return float(request.data.get(key, default))
        except (TypeError, ValueError):
            return default

    score, factors = compute_priority(
        num("structural_risk"), num("population_exposure"),
        num("accessibility"), num("infrastructure_risk"),
        num("evidence_confidence"),
    )
    evidence_refs = request.data.get("evidence_refs") or []
    if isinstance(evidence_refs, str):
        evidence_refs = [x.strip() for x in evidence_refs.split(",") if x.strip()]

    zone = PriorityZone.objects.create(
        disaster=disaster,
        location=request.data.get("location", disaster.location),
        latitude=request.data.get("latitude") or disaster.latitude,
        longitude=request.data.get("longitude") or disaster.longitude,
        structural_risk=factors["structural_risk"],
        population_exposure=factors["population_exposure"],
        vulnerability=num("vulnerability"),
        accessibility=factors["accessibility"],
        infrastructure_risk=factors["infrastructure_risk"],
        evidence_confidence=factors["evidence_confidence"],
        priority_score=score, factors=factors, evidence_refs=evidence_refs,
    )
    log_event(disaster, f"Priority zone {zone.zone_code} generated (score {score})",
              actor=request.user.username, source="Priority Engine",
              evidence_ref=zone.zone_code)
    return Response(PriorityZoneSerializer(zone).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def priority_zone_detail(request, pk):
    try:
        zone = PriorityZone.objects.get(pk=pk)
    except PriorityZone.DoesNotExist:
        return Response({"detail": "Zone not found."}, status=status.HTTP_404_NOT_FOUND)
    data = PriorityZoneSerializer(zone).data
    data["timeline"] = EvidenceEventSerializer(zone.disaster.timeline.all(), many=True).data
    return Response(data)


# --------------------------- Reports ---------------------------
@api_view(["GET", "POST"])
def reports(request):
    if request.method == "GET":
        qs = Report.objects.all()
        disaster_id = request.query_params.get("disaster")
        if disaster_id:
            qs = qs.filter(disaster_id=disaster_id)
        return Response(ReportSerializer(qs, many=True).data)

    serializer = ReportSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    report = serializer.save(author=request.user)
    log_event(report.disaster, f"Field report '{report.title}' submitted",
              actor=request.user.username, source="Report",
              evidence_ref=report.report_code)
    return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)


# --------------------------- Responses ---------------------------
@api_view(["GET", "POST"])
def assignments(request):
    if request.method == "GET":
        qs = ResponseAssignment.objects.all()
        dstatus = request.query_params.get("status")
        if dstatus:
            qs = qs.filter(status=dstatus)
        return Response(ResponseAssignmentSerializer(qs, many=True).data)

    serializer = ResponseAssignmentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    assignment = serializer.save(created_by=request.user)
    log_event(assignment.disaster,
              f"Responder assigned: {assignment.task}",
              actor=request.user.username, source="Response Coordination",
              evidence_ref=assignment.assignment_code)
    return Response(ResponseAssignmentSerializer(assignment).data,
                    status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
def assignment_detail(request, pk):
    try:
        assignment = ResponseAssignment.objects.get(pk=pk)
    except ResponseAssignment.DoesNotExist:
        return Response({"detail": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)
    new_status = request.data.get("status")
    if new_status and new_status in {"assigned", "in_progress", "completed"}:
        assignment.status = new_status
    if "notes" in request.data:
        assignment.notes = request.data["notes"]
    assignment.save()
    log_event(assignment.disaster,
              f"Assignment {assignment.assignment_code} status: {assignment.status}",
              actor=request.user.username, source="Response Management",
              evidence_ref=assignment.assignment_code)
    return Response(ResponseAssignmentSerializer(assignment).data)


# --------------------------- Routes ---------------------------
@api_view(["GET", "POST"])
def plan_route(request):
    if request.method == "GET":
        qs = RoutePlan.objects.all()
        disaster_id = request.query_params.get("disaster")
        if disaster_id:
            qs = qs.filter(disaster_id=disaster_id)
        return Response(RoutePlanSerializer(qs, many=True).data)

    try:
        disaster = Disaster.objects.get(pk=request.data.get("disaster"))
    except Disaster.DoesNotExist:
        return Response({"detail": "Incident not found."}, status=status.HTTP_404_NOT_FOUND)

    def num(key):
        try:
            return float(request.data.get(key))
        except (TypeError, ValueError):
            return None

    slat, slng = num("start_lat"), num("start_lng")
    dlat, dlng = num("dest_lat"), num("dest_lng")
    if None in (slat, slng, dlat, dlng):
        return Response({"detail": "Start and destination coordinates are required."},
                        status=status.HTTP_400_BAD_REQUEST)

    # Use the free OpenStreetMap/OSRM routing service for a real road route.
    # If it is temporarily unavailable, retain a deterministic straight-line
    # fallback rather than failing the emergency-planning workflow.
    distance = haversine_km(slat, slng, dlat, dlng)
    est_minutes = round((distance / 35.0) * 60, 1)
    routing_source = "straight-line fallback"
    route_geometry = [[slat, slng], [dlat, dlng]]
    try:
        osrm = requests.get(
            f"https://router.project-osrm.org/route/v1/driving/{slng},{slat};{dlng},{dlat}",
            params={"overview": "full", "geometries": "geojson", "steps": "false"},
            timeout=8,
            headers={"User-Agent": "RESQAI/1.0"},
        )
        osrm.raise_for_status()
        route_data = osrm.json()
        route0 = (route_data.get("routes") or [None])[0]
        if route0:
            distance = round(float(route0["distance"]) / 1000.0, 2)
            est_minutes = round(float(route0["duration"]) / 60.0, 1)
            routing_source = "OpenStreetMap/OSRM"
            route_geometry = [[point[1], point[0]] for point in route0.get("geometry", {}).get("coordinates", [])]
            if not route_geometry:
                route_geometry = [[slat, slng], [dlat, dlng]]
    except Exception:
        pass

    blocked = list(
        disaster.findings.filter(finding_type="blocked_road")
        .exclude(verification_status="rejected")
        .values_list("label", flat=True)
    )
    if any(f.verification_status in ("confirmed", "corrected")
           for f in disaster.findings.filter(finding_type="blocked_road")):
        route_status = "blocked"
        explanation = ("A verified blocked-road finding intersects this corridor. "
                       "Blocked according to available data.")
    elif blocked:
        route_status = "obstruction"
        explanation = ("Unverified blocked-road findings exist for this incident. "
                       "Potential obstruction reported \u2014 verify before dispatch.")
    else:
        route_status = "passable"
        explanation = (
            f"No blocked-road evidence recorded for this incident. "
            f"Road route calculated with {routing_source}; passable according to "
            "available evidence, but confirm conditions on the ground."
        )

    route = RoutePlan.objects.create(
        disaster=disaster,
        start_location=request.data.get("start_location", ""),
        start_lat=slat, start_lng=slng,
        dest_location=request.data.get("dest_location", ""),
        dest_lat=dlat, dest_lng=dlng,
        distance_km=distance, est_minutes=est_minutes,
        blocked_roads=blocked, route_status=route_status,
        explanation=explanation, created_by=request.user,
    )
    log_event(disaster, f"Route {route.route_code} planned ({route_status})",
              actor=request.user.username, source="Route Planner",
              evidence_ref=route.route_code)
    response_data = RoutePlanSerializer(route).data
    response_data["geometry"] = route_geometry
    response_data["routing_source"] = routing_source
    return Response(response_data, status=status.HTTP_201_CREATED)


# --------------------------- Live external feeds ---------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def earthquakes(request):
    try:
        min_mag = float(request.query_params.get("min_magnitude", 0))
    except (TypeError, ValueError):
        min_mag = 0
    return Response(live_data.get_earthquakes(min_magnitude=min_mag))


@api_view(["GET"])
@permission_classes([AllowAny])
def fires(request):
    map_key = request.query_params.get("map_key")
    return Response(live_data.get_fires(map_key=map_key))


@api_view(["GET"])
@permission_classes([AllowAny])
def system_status(request):
    eq = live_data.get_earthquakes()
    fr = live_data.get_fires()
    return Response({
        "sources": [
            {"name": "Django API", "status": "connected", "connection": "LIVE"},
            {"name": "USGS", "status": eq["status"], "connection": eq["connection"],
             "last_updated": eq.get("last_updated")},
            { "name": "GDACS (India)", "status": fr["status"], "connection": fr["connection"],
             "last_updated": fr.get("last_updated"),
             "message": fr.get("message", "")},
            {"name": "OpenStreetMap", "status": "connected", "connection": "LIVE"},
            {"name": "Google Maps", "status": "optional", "connection": "OPTIONAL",
             "message": "Configured client-side when an API key is provided."},
        ]
    })