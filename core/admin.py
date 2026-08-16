from django.contrib import admin

from .models import (
    Disaster, EvidenceEvent, Finding, ImageAnalysis, PriorityZone,
    Profile, Report, ResponseAssignment, RoutePlan, Verification,
)

for model in (Profile, Disaster, ImageAnalysis, Finding, Verification,
              PriorityZone, Report, ResponseAssignment, RoutePlan, EvidenceEvent):
    admin.site.register(model)