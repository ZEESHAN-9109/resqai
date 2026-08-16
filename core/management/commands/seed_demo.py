"""Seed RESQAI demo accounts, current demo incidents, and historical India data.

The historical rows are clearly marked as demonstration/reference records.
They are not live-feed events and are used to make the dashboard, filters,
evidence timeline and priority views useful during a product demo.
"""
from datetime import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework.authtoken.models import Token

from core.models import (
    Disaster, EvidenceEvent, ImageAnalysis, Finding, PriorityZone,
    Profile, Report, ResponseAssignment,
)
from core.services.priority import compute_priority


HISTORICAL_INCIDENTS = [
    ("Kerala Floods 2018", "flood", "high", "resolved", "Kerala", 10.8505, 76.2711, 2018, 8, 16, 5000000),
    ("Cyclone Fani 2019", "cyclone", "critical", "resolved", "Puri, Odisha", 19.8135, 85.8312, 2019, 5, 3, 1600000),
    ("Assam Floods 2019", "flood", "high", "resolved", "Assam", 26.2006, 92.9376, 2019, 7, 20, 3000000),
    ("Bihar Floods 2019", "flood", "high", "resolved", "Bihar", 25.0961, 85.3131, 2019, 8, 15, 7000000),
    ("Mumbai Floods 2019", "flood", "high", "resolved", "Mumbai, Maharashtra", 19.0760, 72.8777, 2019, 7, 2, 2000000),
    ("Cyclone Amphan 2020", "cyclone", "critical", "resolved", "West Bengal", 22.9868, 87.8550, 2020, 5, 20, 13000000),
    ("Hyderabad Floods 2020", "flood", "high", "resolved", "Hyderabad, Telangana", 17.3850, 78.4867, 2020, 10, 13, 2500000),
    ("Cyclone Tauktae 2021", "cyclone", "critical", "resolved", "Gujarat", 22.2587, 71.1924, 2021, 5, 17, 2000000),
    ("Chamoli Flash Flood 2021", "flood", "critical", "resolved", "Chamoli, Uttarakhand", 30.4020, 79.3200, 2021, 2, 7, 5000),
    ("Cyclone Yaas 2021", "cyclone", "high", "resolved", "Balasore, Odisha", 21.4934, 86.9135, 2021, 5, 26, 6000000),
    ("Assam Floods 2021", "flood", "high", "resolved", "Assam", 26.2006, 92.9376, 2021, 7, 20, 7000000),
    ("Cyclone Asani 2022", "cyclone", "high", "resolved", "Andhra Pradesh coast", 16.5062, 80.6480, 2022, 5, 11, 1000000),
    ("Assam Floods 2022", "flood", "critical", "resolved", "Assam", 26.2006, 92.9376, 2022, 6, 20, 5500000),
    ("Himachal Monsoon Floods 2022", "flood", "high", "resolved", "Himachal Pradesh", 31.1048, 77.1734, 2022, 7, 8, 300000),
    ("Cyclone Biparjoy 2023", "cyclone", "critical", "resolved", "Kutch, Gujarat", 23.7337, 69.8597, 2023, 6, 15, 3500000),
    ("Delhi Floods 2023", "flood", "high", "resolved", "Delhi", 28.6139, 77.2090, 2023, 7, 13, 2000000),
    ("Himachal Pradesh Floods 2023", "flood", "critical", "resolved", "Shimla, Himachal Pradesh", 31.1048, 77.1734, 2023, 8, 14, 1500000),
    ("Sikkim Glacial Lake Outburst Flood 2023", "flood", "critical", "resolved", "Sikkim", 27.5330, 88.6139, 2023, 10, 4, 100000),
    ("Cyclone Michaung 2023", "cyclone", "high", "resolved", "Chennai, Tamil Nadu", 13.0827, 80.2707, 2023, 12, 4, 1500000),
    ("Wayanad Landslides 2024", "landslide", "critical", "resolved", "Wayanad, Kerala", 11.6854, 76.1320, 2024, 7, 30, 15000),
    ("Cyclone Remal 2024", "cyclone", "high", "resolved", "West Bengal", 22.5726, 88.3639, 2024, 5, 27, 7000000),
    ("Gujarat Floods 2024", "flood", "high", "resolved", "Gujarat", 22.2587, 71.1924, 2024, 8, 29, 300000),
    ("Assam Floods 2024", "flood", "high", "resolved", "Assam", 26.2006, 92.9376, 2024, 6, 20, 6000000),
    ("Odisha Cyclone Dana 2024", "cyclone", "high", "resolved", "Odisha coast", 20.9517, 85.0985, 2024, 10, 25, 1000000),
    ("Sikkim Landslide Emergency 2025", "landslide", "high", "resolved", "Sikkim", 27.5330, 88.6139, 2025, 6, 13, 25000),
]


class Command(BaseCommand):
    help = "Seed demo accounts, current incidents, and historical India incidents."

    def _user(self, email, name, role, password, staff=False):
        user, created = User.objects.get_or_create(
            username=email, defaults={"email": email}
        )
        if created:
            user.set_password(password)
            user.is_staff = staff
            user.is_superuser = staff
            user.save()
        Profile.objects.get_or_create(
            user=user, defaults={"role": role, "full_name": name}
        )
        Token.objects.get_or_create(user=user)
        return user

    def _set_date(self, obj, year, month, day):
        dt = timezone.make_aware(datetime(year, month, day, 10, 0, 0))
        Disaster.objects.filter(pk=obj.pk).update(created_at=dt, updated_at=dt)

    def _ensure_current_demo(self, admin, responder):
        d1, _ = Disaster.objects.get_or_create(
            name="Coastal District Flood (Demo)",
            defaults=dict(
                disaster_type="flood", severity="high", status="active",
                location="Riverside Ward, Coastal District",
                latitude=19.0760, longitude=72.8777,
                description="Demonstration incident for platform walkthrough. "
                            "Operator-entered; not live external data.",
                affected_population=5400, created_by=admin,
            ),
        )
        d2, _ = Disaster.objects.get_or_create(
            name="Hillslope Landslide (Demo)",
            defaults=dict(
                disaster_type="landslide", severity="critical", status="active",
                location="North Ridge, Hill Station",
                latitude=30.7333, longitude=76.7794,
                description="Demonstration incident for platform walkthrough. "
                            "Operator-entered; not live external data.",
                affected_population=1200, created_by=admin,
            ),
        )

        for d in (d1, d2):
            EvidenceEvent.objects.get_or_create(
                disaster=d,
                action=f"Incident '{d.name}' created",
                defaults=dict(actor=admin.username, source="Operator",
                              evidence_ref=d.incident_code),
            )

        analysis, _ = ImageAnalysis.objects.get_or_create(
            disaster=d1,
            model_used="demo",
            defaults=dict(
                image="analysis/placeholder.txt",
                overall_confidence=0.71,
                summary="Possible structural and road impacts.",
                status="completed",
                created_by=admin,
            ),
        )
        f1, _ = Finding.objects.get_or_create(
            analysis=analysis, disaster=d1, finding_type="blocked_road",
            label="Debris across arterial road",
            defaults=dict(location_hint="Lower frame, centre", confidence=0.68,
                          evidence="Apparent debris and standing water on carriageway."),
        )
        Finding.objects.get_or_create(
            analysis=analysis, disaster=d1, finding_type="damaged_building",
            label="Possible partial roof collapse",
            defaults=dict(location_hint="Right edge", confidence=0.62,
                          evidence="Irregular roofline consistent with structural damage."),
        )
        EvidenceEvent.objects.get_or_create(
            disaster=d1, action="AI analysis completed (2 findings)",
            defaults=dict(actor="AI (decision-support)", source="demo",
                          evidence_ref=analysis.analysis_code),
        )

        score, factors = compute_priority(78, 74, 66, 71, 71)
        zone, _ = PriorityZone.objects.get_or_create(
            disaster=d1, location="Riverside Ward Block C",
            defaults=dict(
                latitude=19.078, longitude=72.879,
                structural_risk=78, population_exposure=74, vulnerability=69,
                accessibility=66, infrastructure_risk=71,
                evidence_confidence=71, priority_score=score, factors=factors,
                evidence_refs=[analysis.analysis_code, d1.incident_code],
            ),
        )
        EvidenceEvent.objects.get_or_create(
            disaster=d1, action=f"Priority zone {zone.zone_code} generated (score {score})",
            defaults=dict(actor=admin.username, source="Priority Engine",
                          evidence_ref=zone.zone_code),
        )

        Report.objects.get_or_create(
            disaster=d1, title="Waterlogging on main access road",
            defaults=dict(
                report_type="infrastructure",
                description="Field team reports water on the main access road.",
                author=responder,
            ),
        )
        ResponseAssignment.objects.get_or_create(
            disaster=d1, task="Verify structural damage in Block C",
            defaults=dict(
                responder=responder, responder_name="Ravi Responder",
                role="field_responder", priority="high", status="assigned",
                zone=zone, created_by=admin,
            ),
        )
        return d1, d2

    def _seed_historical(self, admin):
        created = 0
        for (name, dtype, severity, status, location, lat, lng,
             year, month, day, affected) in HISTORICAL_INCIDENTS:
            incident, was_created = Disaster.objects.get_or_create(
                name=name,
                defaults=dict(
                    disaster_type=dtype,
                    severity=severity,
                    status=status,
                    location=location,
                    latitude=lat,
                    longitude=lng,
                    description=(
                        "Historical India incident reference record for demo use. "
                        "This is not a live external-feed event."
                    ),
                    affected_population=affected,
                    created_by=admin,
                ),
            )
            self._set_date(incident, year, month, day)
            if was_created:
                created += 1

            EvidenceEvent.objects.get_or_create(
                disaster=incident,
                action="Historical incident added to demo evidence timeline",
                defaults=dict(
                    actor="RESQAI demo dataset",
                    source="Historical reference",
                    evidence_ref=incident.incident_code,
                ),
            )

            # Give historical records useful map/priority content without
            # pretending that these values are live field assessments.
            if not PriorityZone.objects.filter(disaster=incident).exists():
                base = 55 + (incident.id % 30)
                score, factors = compute_priority(
                    base, min(95, base + 4), min(95, base - 2),
                    max(30, 100 - base), min(95, base + 1)
                )
                PriorityZone.objects.create(
                    disaster=incident,
                    location=f"{location} priority area",
                    latitude=lat,
                    longitude=lng,
                    structural_risk=base,
                    population_exposure=min(95, base + 4),
                    vulnerability=min(95, base - 2),
                    accessibility=max(30, 100 - base),
                    infrastructure_risk=min(95, base + 1),
                    evidence_confidence=70,
                    priority_score=score,
                    verification_status="confirmed",
                    factors=factors,
                    evidence_refs=[incident.incident_code],
                )

        return created

    def handle(self, *args, **opts):
        admin = self._user("demo@resqai.io", "Demo Commander",
                           "administrator", "demo12345", staff=True)
        self._user("analyst@resqai.io", "Ada Analyst",
                   "analyst", "demo12345")
        responder = self._user("field@resqai.io", "Ravi Responder",
                               "field_responder", "demo12345")

        self._ensure_current_demo(admin, responder)
        created = self._seed_historical(admin)

        self.stdout.write(self.style.SUCCESS(
            f"Demo accounts ensured; {created} historical India incidents added."
        ))
        self.stdout.write("Login: demo@resqai.io / demo12345")
