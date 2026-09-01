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

    # ============================================================
    # 2022 — from 02 September 2022 onward
    # ============================================================

    (
        "Dharchula Cloudburst",
        "flood",
        "high",
        "resolved",
        "Dharchula, Uttarakhand",
        30.0833,
        80.3500,
        2022,
        9,
        10,
        5000,
    ),

    (
        "Bengaluru Urban Floods",
        "flood",
        "high",
        "resolved",
        "Bengaluru, Karnataka",
        12.9716,
        77.5946,
        2022,
        9,
        5,
        50000,
    ),

    (
        "Himachal Pradesh Heavy Rainfall and Landslides",
        "landslide",
        "high",
        "resolved",
        "Himachal Pradesh",
        31.1048,
        77.1734,
        2022,
        9,
        24,
        15000,
    ),

    (
        "Uttarakhand Heavy Rainfall and Landslides",
        "landslide",
        "high",
        "resolved",
        "Uttarakhand",
        30.0668,
        79.0193,
        2022,
        9,
        27,
        10000,
    ),


    # ============================================================
    # 2023
    # ============================================================

    (
        "Joshimath Land Subsidence",
        "landslide",
        "critical",
        "resolved",
        "Joshimath, Uttarakhand",
        30.5550,
        79.5650,
        2023,
        1,
        2,
        20000,
    ),

    (
        "Cyclone Biparjoy",
        "cyclone",
        "critical",
        "resolved",
        "Kutch, Gujarat",
        23.7337,
        69.8597,
        2023,
        6,
        15,
        3500000,
    ),

    (
        "Assam Monsoon Floods",
        "flood",
        "high",
        "resolved",
        "Assam",
        26.2006,
        92.9376,
        2023,
        6,
        20,
        3000000,
    ),

    (
        "Delhi Yamuna Floods",
        "flood",
        "critical",
        "resolved",
        "Delhi",
        28.6139,
        77.2090,
        2023,
        7,
        13,
        2000000,
    ),

    (
        "Himachal Pradesh Monsoon Floods and Landslides",
        "landslide",
        "critical",
        "resolved",
        "Shimla, Himachal Pradesh",
        31.1048,
        77.1734,
        2023,
        8,
        14,
        1500000,
    ),

    (
        "Uttarakhand Monsoon Floods and Landslides",
        "landslide",
        "critical",
        "resolved",
        "Uttarakhand",
        30.0668,
        79.0193,
        2023,
        8,
        14,
        500000,
    ),

    (
        "Sikkim Glacial Lake Outburst Flood",
        "flood",
        "critical",
        "resolved",
        "North Sikkim",
        27.5330,
        88.6139,
        2023,
        10,
        4,
        22000,
    ),

    (
        "Cyclone Michaung",
        "cyclone",
        "critical",
        "resolved",
        "Chennai, Tamil Nadu",
        13.0827,
        80.2707,
        2023,
        12,
        4,
        1500000,
    ),

    (
        "Andhra Pradesh Floods - Michaung",
        "flood",
        "high",
        "resolved",
        "Vijayawada, Andhra Pradesh",
        16.5062,
        80.6480,
        2023,
        12,
        5,
        500000,
    ),


    # ============================================================
    # 2024
    # ============================================================

    (
        "Cyclone Remal",
        "cyclone",
        "critical",
        "resolved",
        "West Bengal",
        22.5726,
        88.3639,
        2024,
        5,
        27,
        7000000,
    ),

    (
        "Assam Monsoon Floods",
        "flood",
        "high",
        "resolved",
        "Assam",
        26.2006,
        92.9376,
        2024,
        6,
        20,
        6000000,
    ),

    (
        "Manipur Floods",
        "flood",
        "high",
        "resolved",
        "Manipur",
        24.8170,
        93.9368,
        2024,
        5,
        31,
        100000,
    ),

    (
        "Wayanad Landslides",
        "landslide",
        "critical",
        "resolved",
        "Wayanad, Kerala",
        11.6854,
        76.1320,
        2024,
        7,
        30,
        15000,
    ),

    (
        "Uttarakhand Monsoon Landslides",
        "landslide",
        "critical",
        "resolved",
        "Uttarakhand",
        30.0668,
        79.0193,
        2024,
        7,
        31,
        50000,
    ),

    (
        "Tripura Severe Floods",
        "flood",
        "critical",
        "resolved",
        "Agartala, Tripura",
        23.8315,
        91.2868,
        2024,
        8,
        19,
        150000,
    ),

    (
        "Gujarat Severe Floods",
        "flood",
        "critical",
        "resolved",
        "Gujarat",
        22.2587,
        71.1924,
        2024,
        8,
        29,
        300000,
    ),

    (
        "Andhra Pradesh and Telangana Floods",
        "flood",
        "critical",
        "resolved",
        "Vijayawada, Andhra Pradesh",
        16.5062,
        80.6480,
        2024,
        9,
        1,
        300000,
    ),

    (
        "Cyclone Dana",
        "cyclone",
        "high",
        "resolved",
        "Odisha Coast",
        20.9517,
        85.0985,
        2024,
        10,
        25,
        1000000,
    ),

    (
        "Cyclone Fengal",
        "cyclone",
        "high",
        "resolved",
        "Puducherry",
        11.9416,
        79.8083,
        2024,
        11,
        30,
        500000,
    ),


    # ============================================================
    # 2025
    # ============================================================

    (
        "Assam Floods",
        "flood",
        "high",
        "resolved",
        "Assam",
        26.2006,
        92.9376,
        2025,
        6,
        1,
        300000,
    ),

    (
        "Manipur Floods",
        "flood",
        "high",
        "resolved",
        "Manipur",
        24.8170,
        93.9368,
        2025,
        6,
        1,
        100000,
    ),

    (
        "Tripura Floods",
        "flood",
        "high",
        "resolved",
        "Tripura",
        23.8315,
        91.2868,
        2025,
        6,
        1,
        100000,
    ),

    (
        "Kerala Heavy Rainfall and Landslides",
        "landslide",
        "high",
        "resolved",
        "Kerala",
        10.8505,
        76.2711,
        2025,
        7,
        1,
        50000,
    ),

    (
        "Himachal Pradesh Floods and Landslides",
        "landslide",
        "critical",
        "resolved",
        "Himachal Pradesh",
        31.1048,
        77.1734,
        2025,
        8,
        1,
        100000,
    ),

    (
        "Dharali Cloudburst and Flash Flood",
        "flood",
        "critical",
        "resolved",
        "Dharali, Uttarakhand",
        30.9930,
        78.6200,
        2025,
        8,
        5,
        10000,
    ),

    (
        "Kishtwar Cloudburst and Flash Flood",
        "flood",
        "critical",
        "resolved",
        "Kishtwar, Jammu and Kashmir",
        33.3150,
        75.7700,
        2025,
        8,
        14,
        10000,
    ),

    (
        "Jammu and Kashmir Floods and Landslides",
        "flood",
        "critical",
        "resolved",
        "Jammu and Kashmir",
        33.7782,
        76.5762,
        2025,
        8,
        26,
        150000,
    ),

    (
        "Punjab Severe Floods",
        "flood",
        "critical",
        "resolved",
        "Punjab",
        30.9010,
        75.8573,
        2025,
        8,
        27,
        200000,
    ),

    (
        "Maharashtra Monsoon Floods",
        "flood",
        "high",
        "resolved",
        "Maharashtra",
        19.7515,
        75.7139,
        2025,
        9,
        1,
        300000,
    ),

    (
        "Cyclone Montha",
        "cyclone",
        "critical",
        "resolved",
        "Andhra Pradesh",
        16.5000,
        80.6500,
        2025,
        10,
        29,
        100000,
    ),

    (
        "Odisha Cyclone Montha Rainfall",
        "flood",
        "high",
        "resolved",
        "Odisha",
        20.9517,
        85.0985,
        2025,
        10,
        29,
        100000,
    ),


    # ============================================================
    # 2026 — through 02 September 2026
    # ============================================================

    (
        "Assam Floods 2026",
        "flood",
        "critical",
        "active",
        "Assam",
        26.2006,
        92.9376,
        2026,
        7,
        1,
        300000,
    ),

    (
        "Arunachal Pradesh Floods and Landslides",
        "landslide",
        "high",
        "active",
        "Arunachal Pradesh",
        27.0844,
        93.6053,
        2026,
        7,
        1,
        50000,
    ),

    (
        "Gujarat Heavy Rainfall and Floods",
        "flood",
        "high",
        "active",
        "Gujarat",
        22.2587,
        71.1924,
        2026,
        7,
        1,
        100000,
    ),

    (
        "Himachal Pradesh Cloudbursts and Landslides",
        "landslide",
        "critical",
        "active",
        "Himachal Pradesh",
        31.1048,
        77.1734,
        2026,
        8,
        1,
        50000,
    ),

    (
        "Jammu and Kashmir Heavy Rainfall and Landslides",
        "landslide",
        "critical",
        "active",
        "Jammu and Kashmir",
        33.7782,
        76.5762,
        2026,
        7,
        1,
        50000,
    ),

    (
        "Uttarakhand Heavy Rainfall and Landslides",
        "landslide",
        "critical",
        "active",
        "Uttarakhand",
        30.0668,
        79.0193,
        2026,
        7,
        1,
        50000,
    ),

    (
        "Kerala Heavy Rainfall and Landslides",
        "landslide",
        "high",
        "active",
        "Kerala",
        10.8505,
        76.2711,
        2026,
        7,
        1,
        50000,
    ),

    (
        "Northeast India Floods and Landslides",
        "flood",
        "high",
        "active",
        "Northeast India",
        26.1445,
        91.7362,
        2026,
        7,
        20,
        100000,
    ),

    (
        "Odisha Heavy Rainfall and Flooding",
        "flood",
        "high",
        "active",
        "Odisha",
        20.9517,
        85.0985,
        2026,
        8,
        30,
        100000,
    ),

    (
        "West Bengal Heavy Rainfall and Flooding",
        "flood",
        "high",
        "active",
        "West Bengal",
        22.5726,
        88.3639,
        2026,
        8,
        30,
        100000,
    ),

    (
        "Jharkhand Heavy Rainfall and Flooding",
        "flood",
        "high",
        "active",
        "Jharkhand",
        23.6102,
        85.2799,
        2026,
        8,
        30,
        50000,
    ),

    (
        "Chhattisgarh Heavy Rainfall and Flooding",
        "flood",
        "high",
        "active",
        "Chhattisgarh",
        21.2787,
        81.8661,
        2026,
        8,
        31,
        50000,
    ),
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
