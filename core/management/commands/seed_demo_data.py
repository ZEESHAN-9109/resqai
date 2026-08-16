from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import (
    Profile,
    Disaster,
    PriorityZone,
    Report,
    ResponseAssignment,
    RoutePlan,
    EvidenceEvent,
)


class Command(BaseCommand):
    help = "Create demo data for the RESQAI dashboard"

    def handle(self, *args, **options):
        self.stdout.write("Creating RESQAI demo data...")

        # ---------------------------------------------------------
        # USERS
        # ---------------------------------------------------------

        users = {}

        demo_users = [
            {
                "username": "admin_demo",
                "password": "ResqaiDemo123!",
                "role": "administrator",
                "full_name": "RESQAI Administrator",
                "organisation": "RESQAI Command Center",
            },
            {
                "username": "commander_demo",
                "password": "ResqaiDemo123!",
                "role": "incident_commander",
                "full_name": "Incident Commander",
                "organisation": "National Disaster Response",
            },
            {
                "username": "responder_demo",
                "password": "ResqaiDemo123!",
                "role": "field_responder",
                "full_name": "Field Response Team",
                "organisation": "Emergency Response Unit",
            },
            {
                "username": "analyst_demo",
                "password": "ResqaiDemo123!",
                "role": "analyst",
                "full_name": "Disaster Intelligence Analyst",
                "organisation": "RESQAI Analytics",
            },
            {
                "username": "verifier_demo",
                "password": "ResqaiDemo123!",
                "role": "verifier",
                "full_name": "Evidence Verification Officer",
                "organisation": "RESQAI Verification",
            },
        ]

        for data in demo_users:
            user, created = User.objects.get_or_create(
                username=data["username"]
            )

            if created:
                user.set_password(data["password"])
                user.save()

            profile, _ = Profile.objects.get_or_create(user=user)

            profile.role = data["role"]
            profile.full_name = data["full_name"]
            profile.organisation = data["organisation"]
            profile.save()

            users[data["role"]] = user

        admin = users["administrator"]
        commander = users["incident_commander"]
        responder = users["field_responder"]
        analyst = users["analyst"]
        verifier = users["verifier"]

        # ---------------------------------------------------------
        # DISASTERS / INCIDENTS
        # ---------------------------------------------------------

        disasters_data = [
            {
                "name": "Bhubaneswar Urban Flood",
                "disaster_type": "flood",
                "severity": "high",
                "status": "active",
                "location": "Bhubaneswar, Odisha",
                "latitude": 20.2961,
                "longitude": 85.8245,
                "description": (
                    "Heavy rainfall has caused water accumulation "
                    "in several low-lying urban areas."
                ),
                "affected_population": 12500,
            },
            {
                "name": "Cyclone Alert - Odisha Coast",
                "disaster_type": "cyclone",
                "severity": "critical",
                "status": "active",
                "location": "Puri Coast, Odisha",
                "latitude": 19.8135,
                "longitude": 85.8312,
                "description": (
                    "Severe weather conditions detected along the "
                    "Odisha coastline. Emergency teams are monitoring "
                    "the situation."
                ),
                "affected_population": 45000,
            },
            {
                "name": "Ranchi Forest Fire",
                "disaster_type": "fire",
                "severity": "medium",
                "status": "monitoring",
                "location": "Ranchi, Jharkhand",
                "latitude": 23.3441,
                "longitude": 85.3096,
                "description": (
                    "Forest fire activity detected in a remote area. "
                    "Fire response teams are monitoring the perimeter."
                ),
                "affected_population": 1800,
            },
            {
                "name": "Sikkim Landslide",
                "disaster_type": "landslide",
                "severity": "high",
                "status": "resolved",
                "location": "Gangtok, Sikkim",
                "latitude": 27.3389,
                "longitude": 88.6065,
                "description": (
                    "Road obstruction caused by a landslide has "
                    "been cleared by response teams."
                ),
                "affected_population": 900,
            },
        ]

        disasters = {}

        for data in disasters_data:
            disaster, _ = Disaster.objects.get_or_create(
                name=data["name"],
                defaults={
                    **data,
                    "created_by": commander,
                },
            )

            # Keep demo data correct if command is run again.
            for field, value in data.items():
                setattr(disaster, field, value)

            disaster.created_by = commander
            disaster.save()

            disasters[data["name"]] = disaster

        flood = disasters["Bhubaneswar Urban Flood"]
        cyclone = disasters["Cyclone Alert - Odisha Coast"]
        fire = disasters["Ranchi Forest Fire"]
        landslide = disasters["Sikkim Landslide"]

        # ---------------------------------------------------------
        # PRIORITY ZONES
        # ---------------------------------------------------------

        zones = [
            {
                "disaster": flood,
                "location": "Patia Low-Lying Area",
                "latitude": 20.3547,
                "longitude": 85.8267,
                "structural_risk": 72,
                "population_exposure": 85,
                "vulnerability": 78,
                "accessibility": 45,
                "infrastructure_risk": 70,
                "evidence_confidence": 91,
                "priority_score": 82,
                "verification_status": "confirmed",
            },
            {
                "disaster": flood,
                "location": "Old Town Waterlogging Zone",
                "latitude": 20.2510,
                "longitude": 85.8330,
                "structural_risk": 68,
                "population_exposure": 90,
                "vulnerability": 84,
                "accessibility": 38,
                "infrastructure_risk": 76,
                "evidence_confidence": 88,
                "priority_score": 86,
                "verification_status": "confirmed",
            },
            {
                "disaster": cyclone,
                "location": "Puri Coastal Evacuation Zone",
                "latitude": 19.7983,
                "longitude": 85.8245,
                "structural_risk": 80,
                "population_exposure": 94,
                "vulnerability": 82,
                "accessibility": 62,
                "infrastructure_risk": 75,
                "evidence_confidence": 93,
                "priority_score": 91,
                "verification_status": "confirmed",
            },
            {
                "disaster": fire,
                "location": "Ranchi Forest Perimeter",
                "latitude": 23.3615,
                "longitude": 85.2945,
                "structural_risk": 55,
                "population_exposure": 42,
                "vulnerability": 48,
                "accessibility": 52,
                "infrastructure_risk": 40,
                "evidence_confidence": 86,
                "priority_score": 59,
                "verification_status": "confirmed",
            },
        ]

        zone_objects = []

        for data in zones:
            zone, _ = PriorityZone.objects.get_or_create(
                disaster=data["disaster"],
                location=data["location"],
                defaults=data,
            )

            for field, value in data.items():
                if field != "disaster":
                    setattr(zone, field, value)

            zone.save()
            zone_objects.append(zone)

        # ---------------------------------------------------------
        # REPORTS
        # ---------------------------------------------------------

        reports = [
            {
                "disaster": flood,
                "title": "Severe waterlogging reported",
                "report_type": "incident",
                "description": (
                    "Multiple roads in the Patia area have reported "
                    "significant water accumulation."
                ),
                "verification_status": "confirmed",
                "author": analyst,
            },
            {
                "disaster": flood,
                "title": "Emergency shelter requirement",
                "report_type": "resource_requirement",
                "description": (
                    "Temporary shelters and drinking water are required "
                    "for affected residents."
                ),
                "verification_status": "confirmed",
                "author": commander,
            },
            {
                "disaster": cyclone,
                "title": "Coastal evacuation warning",
                "report_type": "incident",
                "description": (
                    "Residents in vulnerable coastal areas should "
                    "move toward designated evacuation centers."
                ),
                "verification_status": "confirmed",
                "author": verifier,
            },
            {
                "disaster": fire,
                "title": "Forest fire perimeter monitoring",
                "report_type": "infrastructure",
                "description": (
                    "Fire response teams are monitoring the affected "
                    "forest perimeter."
                ),
                "verification_status": "unverified",
                "author": analyst,
            },
        ]

        for data in reports:
            Report.objects.get_or_create(
                disaster=data["disaster"],
                title=data["title"],
                defaults=data,
            )

        # ---------------------------------------------------------
        # RESPONSE ASSIGNMENTS
        # ---------------------------------------------------------

        flood_zone = PriorityZone.objects.filter(
            disaster=flood
        ).order_by("-priority_score").first()

        cyclone_zone = PriorityZone.objects.filter(
            disaster=cyclone
        ).order_by("-priority_score").first()

        assignments = [
            {
                "disaster": flood,
                "responder": responder,
                "responder_name": "Flood Response Team",
                "role": "field_responder",
                "priority": "high",
                "task": "Inspect flooded roads and assist stranded residents",
                "status": "in_progress",
                "notes": "Focus on low-lying areas.",
                "zone": flood_zone,
                "created_by": commander,
            },
            {
                "disaster": cyclone,
                "responder": responder,
                "responder_name": "Coastal Emergency Team",
                "role": "field_responder",
                "priority": "critical",
                "task": "Support coastal evacuation operations",
                "status": "assigned",
                "notes": "Coordinate with local authorities.",
                "zone": cyclone_zone,
                "created_by": commander,
            },
            {
                "disaster": fire,
                "responder": responder,
                "responder_name": "Fire Monitoring Team",
                "role": "field_responder",
                "priority": "medium",
                "task": "Monitor fire perimeter and report changes",
                "status": "assigned",
                "notes": "Maintain regular status updates.",
                "zone": None,
                "created_by": commander,
            },
        ]

        for data in assignments:
            ResponseAssignment.objects.get_or_create(
                disaster=data["disaster"],
                task=data["task"],
                defaults=data,
            )

        # ---------------------------------------------------------
        # ROUTE PLANS
        # ---------------------------------------------------------

        routes = [
            {
                "disaster": flood,
                "start_location": "RESQAI Command Center",
                "start_lat": 20.2961,
                "start_lng": 85.8245,
                "dest_location": "Patia Low-Lying Area",
                "dest_lat": 20.3547,
                "dest_lng": 85.8267,
                "distance_km": 8.4,
                "est_minutes": 24,
                "blocked_roads": [
                    "Patia Main Road - partial obstruction"
                ],
                "route_status": "obstruction",
                "explanation": (
                    "Route is usable with caution. A partial road "
                    "obstruction has been reported."
                ),
                "created_by": commander,
            },
            {
                "disaster": cyclone,
                "start_location": "Puri Emergency Center",
                "start_lat": 19.8135,
                "start_lng": 85.8312,
                "dest_location": "Coastal Evacuation Zone",
                "dest_lat": 19.7983,
                "dest_lng": 85.8245,
                "distance_km": 3.2,
                "est_minutes": 12,
                "blocked_roads": [],
                "route_status": "passable",
                "explanation": (
                    "Available route appears passable according "
                    "to current incident information."
                ),
                "created_by": commander,
            },
        ]

        for data in routes:
            RoutePlan.objects.get_or_create(
                disaster=data["disaster"],
                start_location=data["start_location"],
                dest_location=data["dest_location"],
                defaults=data,
            )

        # ---------------------------------------------------------
        # EVIDENCE / TIMELINE EVENTS
        # ---------------------------------------------------------

        timeline_events = [
            {
                "disaster": flood,
                "actor": "RESQAI Monitoring System",
                "action": "Flood incident detected",
                "source": "Demo Sensor Feed",
                "evidence_ref": "DEMO-FLD-001",
            },
            {
                "disaster": flood,
                "actor": "Incident Commander",
                "action": "Response team assigned to priority zone",
                "source": "Command Center",
                "evidence_ref": "DEMO-FLD-002",
            },
            {
                "disaster": flood,
                "actor": "Field Response Team",
                "action": "Field assessment started",
                "source": "Field Report",
                "evidence_ref": "DEMO-FLD-003",
            },
            {
                "disaster": cyclone,
                "actor": "RESQAI Monitoring System",
                "action": "Cyclone risk upgraded to critical",
                "source": "Weather Feed",
                "evidence_ref": "DEMO-CYC-001",
            },
            {
                "disaster": cyclone,
                "actor": "Incident Commander",
                "action": "Coastal evacuation response initiated",
                "source": "Command Center",
                "evidence_ref": "DEMO-CYC-002",
            },
            {
                "disaster": fire,
                "actor": "Fire Monitoring Team",
                "action": "Fire perimeter monitoring active",
                "source": "Field Report",
                "evidence_ref": "DEMO-FIR-001",
            },
            {
                "disaster": landslide,
                "actor": "Response Team",
                "action": "Blocked road cleared",
                "source": "Field Report",
                "evidence_ref": "DEMO-LND-001",
            },
        ]

        for data in timeline_events:
            EvidenceEvent.objects.get_or_create(
                disaster=data["disaster"],
                action=data["action"],
                defaults=data,
            )

        # ---------------------------------------------------------
        # FINISHED
        # ---------------------------------------------------------

        self.stdout.write(
            self.style.SUCCESS(
                "RESQAI demo data created successfully."
            )
        )

        self.stdout.write("")
        self.stdout.write("Demo accounts:")
        self.stdout.write("  admin_demo / ResqaiDemo123!")
        self.stdout.write("  commander_demo / ResqaiDemo123!")
        self.stdout.write("  responder_demo / ResqaiDemo123!")
        self.stdout.write("  analyst_demo / ResqaiDemo123!")
        self.stdout.write("  verifier_demo / ResqaiDemo123!")