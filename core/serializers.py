from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    Disaster, EvidenceEvent, Finding, ImageAnalysis, PriorityZone,
    Profile, Report, ResponseAssignment, RoutePlan, Verification,
)


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)
    role = serializers.ChoiceField(
        choices=["administrator", "incident_commander", "field_responder", "analyst", "verifier"],
        default="analyst",
    )

    def validate_email(self, value):
        if User.objects.filter(username=value).exists() or User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def create(self, validated):
        user = User.objects.create_user(
            username=validated["email"],
            email=validated["email"],
            password=validated["password"],
        )
        parts = validated["full_name"].split(" ", 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ""
        user.save()
        Profile.objects.create(
            user=user, role=validated["role"], full_name=validated["full_name"]
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role"]

    def get_role(self, obj):
        return getattr(getattr(obj, "profile", None), "role", "analyst")

    def get_full_name(self, obj):
        prof = getattr(obj, "profile", None)
        if prof and prof.full_name:
            return prof.full_name
        return obj.get_full_name() or obj.username


class DisasterSerializer(serializers.ModelSerializer):
    incident_code = serializers.CharField(read_only=True)
    findings_count = serializers.SerializerMethodField()
    zones_count = serializers.SerializerMethodField()

    class Meta:
        model = Disaster
        fields = [
            "id", "incident_code", "name", "disaster_type", "severity", "status",
            "location", "latitude", "longitude", "description", "affected_population",
            "findings_count", "zones_count", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_findings_count(self, obj):
        return obj.findings.count()

    def get_zones_count(self, obj):
        return obj.priority_zones.count()


class FindingSerializer(serializers.ModelSerializer):
    finding_code = serializers.CharField(read_only=True)
    analysis_code = serializers.CharField(source="analysis.analysis_code", read_only=True)
    disaster_name = serializers.CharField(source="disaster.name", read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Finding
        fields = [
            "id", "finding_code", "analysis", "analysis_code", "disaster", "disaster_name",
            "finding_type", "label", "location_hint", "confidence", "evidence",
            "verification_status", "image_url", "created_at",
        ]

    def get_image_url(self, obj):
        try:
            return obj.analysis.image.url
        except Exception:
            return ""


class ImageAnalysisSerializer(serializers.ModelSerializer):
    analysis_code = serializers.CharField(read_only=True)
    findings = FindingSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    disaster_name = serializers.CharField(source="disaster.name", read_only=True)
    counts = serializers.SerializerMethodField()

    class Meta:
        model = ImageAnalysis
        fields = [
            "id", "analysis_code", "disaster", "disaster_name", "image_url",
            "overall_confidence", "summary", "model_used", "status", "error",
            "counts", "findings", "created_at",
        ]

    def get_image_url(self, obj):
        return obj.image.url if obj.image else ""

    def get_counts(self, obj):
        f = obj.findings.all()
        return {
            "damaged_buildings": sum(1 for x in f if x.finding_type == "damaged_building"),
            "blocked_roads": sum(1 for x in f if x.finding_type == "blocked_road"),
            "service_disruptions": sum(1 for x in f if x.finding_type == "service_disruption"),
        }


class VerificationSerializer(serializers.ModelSerializer):
    verified_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Verification
        fields = [
            "id", "finding", "action", "correct_classification", "reason",
            "notes", "verified_by_name", "created_at",
        ]

    def get_verified_by_name(self, obj):
        return obj.verified_by.username if obj.verified_by else "Unknown"


class PriorityZoneSerializer(serializers.ModelSerializer):
    zone_code = serializers.CharField(read_only=True)
    disaster_name = serializers.CharField(source="disaster.name", read_only=True)

    class Meta:
        model = PriorityZone
        fields = [
            "id", "zone_code", "disaster", "disaster_name", "location",
            "latitude", "longitude", "structural_risk", "population_exposure",
            "vulnerability", "accessibility", "infrastructure_risk",
            "evidence_confidence", "priority_score", "verification_status",
            "evidence_refs", "factors", "created_at", "updated_at",
        ]


class ReportSerializer(serializers.ModelSerializer):
    report_code = serializers.CharField(read_only=True)
    author_name = serializers.SerializerMethodField()
    disaster_name = serializers.CharField(source="disaster.name", read_only=True)

    class Meta:
        model = Report
        fields = [
            "id", "report_code", "disaster", "disaster_name", "title",
            "report_type", "description", "verification_status",
            "author_name", "created_at",
        ]

    def get_author_name(self, obj):
        return obj.author.username if obj.author else "Unknown"


class ResponseAssignmentSerializer(serializers.ModelSerializer):
    assignment_code = serializers.CharField(read_only=True)
    disaster_name = serializers.CharField(source="disaster.name", read_only=True)

    class Meta:
        model = ResponseAssignment
        fields = [
            "id", "assignment_code", "disaster", "disaster_name", "responder",
            "responder_name", "role", "priority", "task", "status", "notes",
            "zone", "created_at", "updated_at",
        ]


class RoutePlanSerializer(serializers.ModelSerializer):
    route_code = serializers.CharField(read_only=True)
    disaster_name = serializers.CharField(source="disaster.name", read_only=True)
    route_status_display = serializers.CharField(source="get_route_status_display", read_only=True)

    class Meta:
        model = RoutePlan
        fields = [
            "id", "route_code", "disaster", "disaster_name", "start_location",
            "start_lat", "start_lng", "dest_location", "dest_lat", "dest_lng",
            "distance_km", "est_minutes", "blocked_roads", "route_status",
            "route_status_display", "explanation", "created_at",
        ]


class EvidenceEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceEvent
        fields = ["id", "disaster", "timestamp", "actor", "action", "source", "evidence_ref"]