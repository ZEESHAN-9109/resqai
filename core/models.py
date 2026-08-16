from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

ROLE_CHOICES = [
    ("administrator", "Administrator"),
    ("incident_commander", "Incident Commander"),
    ("field_responder", "Field Responder"),
    ("analyst", "Analyst"),
    ("verifier", "Verifier"),
]

DISASTER_TYPES = [
    ("flood", "Flood"),
    ("cyclone", "Cyclone"),
    ("earthquake", "Earthquake"),
    ("fire", "Fire"),
    ("landslide", "Landslide"),
    ("other", "Other"),
]

SEVERITY_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("critical", "Critical"),
]

INCIDENT_STATUS = [
    ("active", "Active"),
    ("monitoring", "Monitoring"),
    ("resolved", "Resolved"),
]

FINDING_TYPES = [
    ("damaged_building", "Damaged Building"),
    ("blocked_road", "Blocked Road"),
    ("service_disruption", "Service Disruption"),
    ("other", "Other"),
]

VERIFICATION_STATUS = [
    ("unverified", "Unverified"),
    ("confirmed", "Confirmed"),
    ("corrected", "Corrected"),
    ("rejected", "Rejected"),
]


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default="analyst")
    full_name = models.CharField(max_length=150, blank=True)
    organisation = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Disaster(models.Model):
    name = models.CharField(max_length=200)
    disaster_type = models.CharField(max_length=20, choices=DISASTER_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="medium")
    status = models.CharField(max_length=12, choices=INCIDENT_STATUS, default="active")
    location = models.CharField(max_length=250)
    latitude = models.FloatField()
    longitude = models.FloatField()
    description = models.TextField(blank=True)
    affected_population = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="disasters")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def incident_code(self):
        return f"INC-{self.id:04d}"


class ImageAnalysis(models.Model):
    disaster = models.ForeignKey(Disaster, on_delete=models.CASCADE, related_name="analyses")
    image = models.ImageField(upload_to="analysis/")
    overall_confidence = models.FloatField(default=0.0)
    summary = models.TextField(blank=True)
    model_used = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, default="completed")
    error = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def analysis_code(self):
        return f"IMG-{self.id:04d}"


class Finding(models.Model):
    analysis = models.ForeignKey(ImageAnalysis, on_delete=models.CASCADE, related_name="findings")
    disaster = models.ForeignKey(Disaster, on_delete=models.CASCADE, related_name="findings")
    finding_type = models.CharField(max_length=30, choices=FINDING_TYPES)
    label = models.CharField(max_length=200)
    location_hint = models.CharField(max_length=250, blank=True)
    confidence = models.FloatField(default=0.0)
    evidence = models.TextField(blank=True)
    verification_status = models.CharField(max_length=12, choices=VERIFICATION_STATUS, default="unverified")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def finding_code(self):
        return f"F-{self.id:04d}"


class Verification(models.Model):
    ACTION_CHOICES = [
        ("confirm", "Confirm"),
        ("correct", "Correct"),
        ("reject", "Reject"),
    ]
    finding = models.ForeignKey(Finding, on_delete=models.CASCADE, related_name="verifications")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    correct_classification = models.CharField(max_length=30, choices=FINDING_TYPES, blank=True)
    reason = models.CharField(max_length=250, blank=True)
    notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class PriorityZone(models.Model):
    disaster = models.ForeignKey(Disaster, on_delete=models.CASCADE, related_name="priority_zones")
    location = models.CharField(max_length=250)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    structural_risk = models.FloatField(default=0.0)
    population_exposure = models.FloatField(default=0.0)
    vulnerability = models.FloatField(default=0.0)
    accessibility = models.FloatField(default=0.0)
    infrastructure_risk = models.FloatField(default=0.0)
    evidence_confidence = models.FloatField(default=0.0)
    priority_score = models.FloatField(default=0.0)
    verification_status = models.CharField(max_length=12, choices=VERIFICATION_STATUS, default="unverified")
    evidence_refs = models.JSONField(default=list, blank=True)
    factors = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority_score"]

    @property
    def zone_code(self):
        return f"P-{self.id:04d}"


class Report(models.Model):
    REPORT_TYPES = [
        ("incident", "Incident"),
        ("damage", "Damage"),
        ("casualty", "Casualty"),
        ("infrastructure", "Infrastructure"),
        ("rescue_request", "Rescue Request"),
        ("resource_requirement", "Resource Requirement"),
        ("other", "Other"),
    ]
    disaster = models.ForeignKey(Disaster, on_delete=models.CASCADE, related_name="reports")
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=25, choices=REPORT_TYPES, default="incident")
    description = models.TextField()
    verification_status = models.CharField(max_length=12, choices=VERIFICATION_STATUS, default="unverified")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def report_code(self):
        return f"REP-{self.id:04d}"


class ResponseAssignment(models.Model):
    STATUS_CHOICES = [
        ("assigned", "Assigned"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]
    disaster = models.ForeignKey(Disaster, on_delete=models.CASCADE, related_name="assignments")
    responder = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="assignments")
    responder_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default="field_responder")
    priority = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="medium")
    task = models.CharField(max_length=250)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="assigned")
    notes = models.TextField(blank=True)
    zone = models.ForeignKey(PriorityZone, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_assignments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def assignment_code(self):
        return f"TASK-{self.id:04d}"


class RoutePlan(models.Model):
    ROUTE_STATUS = [
        ("passable", "Passable according to available data"),
        ("obstruction", "Potential obstruction reported"),
        ("blocked", "Blocked according to available data"),
        ("unavailable", "Route information unavailable"),
    ]
    disaster = models.ForeignKey(Disaster, on_delete=models.CASCADE, related_name="routes")
    start_location = models.CharField(max_length=200)
    start_lat = models.FloatField()
    start_lng = models.FloatField()
    dest_location = models.CharField(max_length=200)
    dest_lat = models.FloatField()
    dest_lng = models.FloatField()
    distance_km = models.FloatField(default=0.0)
    est_minutes = models.FloatField(default=0.0)
    blocked_roads = models.JSONField(default=list, blank=True)
    route_status = models.CharField(max_length=15, choices=ROUTE_STATUS, default="unavailable")
    explanation = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def route_code(self):
        return f"ROUTE-{self.id:04d}"


class EvidenceEvent(models.Model):
    disaster = models.ForeignKey(Disaster, on_delete=models.CASCADE, related_name="timeline")
    timestamp = models.DateTimeField(auto_now_add=True)
    actor = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=250)
    source = models.CharField(max_length=100, blank=True)
    evidence_ref = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ["-timestamp"]