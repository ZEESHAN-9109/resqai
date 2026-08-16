from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.utils import timezone as dj_timezone

from core.models import Disaster


HISTORICAL_INCIDENTS = [
    ("Uttarakhand Flash Floods", "flood", "critical", "resolved", "Chamoli, Uttarakhand", 30.41, 79.32, 20000, "2021-02-07", "Flash flooding and debris flow in the Rishi Ganga and Dhauliganga valleys."),
    ("Cyclone Yaas", "cyclone", "high", "resolved", "Odisha and West Bengal", 21.50, 87.00, 1500000, "2021-05-26", "Severe cyclonic storm affecting coastal Odisha and West Bengal."),
    ("Kerala Floods", "flood", "critical", "resolved", "Kerala", 10.85, 76.27, 5000000, "2018-08-15", "Major monsoon flooding and landslides across Kerala."),
    ("Mumbai Floods", "flood", "high", "resolved", "Mumbai, Maharashtra", 19.08, 72.88, 1000000, "2017-08-29", "Extreme rainfall caused widespread urban flooding in Mumbai."),
    ("Chennai Floods", "flood", "critical", "resolved", "Chennai, Tamil Nadu", 13.08, 80.27, 1800000, "2015-12-02", "Severe northeast monsoon flooding affected Chennai and surrounding districts."),
    ("Kashmir Floods", "flood", "critical", "resolved", "Srinagar, Jammu and Kashmir", 34.08, 74.80, 1800000, "2014-09-07", "River flooding inundated large parts of the Kashmir Valley."),
    ("Cyclone Hudhud", "cyclone", "high", "resolved", "Visakhapatnam, Andhra Pradesh", 17.69, 83.22, 900000, "2014-10-12", "Very severe cyclonic storm made landfall near Visakhapatnam."),
    ("Cyclone Phailin", "cyclone", "critical", "resolved", "Ganjam, Odisha", 19.40, 84.80, 11000000, "2013-10-12", "Very severe cyclonic storm made landfall on the Odisha coast."),
    ("Uttarakhand Floods", "flood", "critical", "resolved", "Kedarnath, Uttarakhand", 30.73, 79.07, 400000, "2013-06-16", "Extreme rainfall, flash floods and landslides affected Uttarakhand."),
    ("Leh Cloudburst", "flood", "high", "resolved", "Leh, Ladakh", 34.15, 77.58, 30000, "2010-08-06", "Cloudburst triggered flash floods and debris flows around Leh."),
    ("Mumbai Monsoon Floods", "flood", "critical", "resolved", "Mumbai, Maharashtra", 19.08, 72.88, 2000000, "2005-07-26", "Exceptional rainfall caused catastrophic urban flooding in Mumbai."),
    ("Indian Ocean Tsunami", "other", "critical", "resolved", "Andaman and Nicobar Islands", 11.74, 92.66, 2000000, "2004-12-26", "Indian Ocean tsunami severely affected coastal India and the Andaman and Nicobar Islands."),
    ("Gujarat Earthquake", "earthquake", "critical", "resolved", "Bhuj, Gujarat", 23.25, 69.67, 20000000, "2001-01-26", "Magnitude 7.7 earthquake caused widespread structural damage in Gujarat."),
    ("Latur Earthquake", "earthquake", "critical", "resolved", "Latur, Maharashtra", 18.41, 76.56, 1000000, "1993-09-30", "Major earthquake struck Latur and Osmanabad districts."),
    ("Uttarkashi Earthquake", "earthquake", "high", "resolved", "Uttarkashi, Uttarakhand", 30.73, 78.45, 150000, "1991-10-20", "Earthquake caused significant damage across Uttarkashi district."),
    ("Odisha Super Cyclone", "cyclone", "critical", "resolved", "Jagatsinghpur, Odisha", 20.27, 86.17, 15000000, "1999-10-29", "Extremely severe cyclonic storm devastated coastal Odisha."),
    ("Cyclone Amphan", "cyclone", "critical", "resolved", "Kolkata and South 24 Parganas, West Bengal", 22.57, 88.36, 13000000, "2020-05-20", "Super cyclonic storm affected West Bengal and adjoining eastern India."),
    ("Assam Floods", "flood", "high", "resolved", "Guwahati and Assam", 26.14, 91.74, 7000000, "2022-06-20", "Severe monsoon flooding affected Assam and the Brahmaputra basin."),
    ("Himachal Pradesh Monsoon Floods", "flood", "critical", "resolved", "Shimla, Himachal Pradesh", 31.10, 77.17, 300000, "2023-08-14", "Intense monsoon rainfall triggered flash floods and landslides."),
    ("Sikkim Glacial Lake Outburst Flood", "flood", "critical", "resolved", "North Sikkim", 27.99, 88.76, 100000, "2023-10-04", "South Lhonak Lake outburst caused severe flooding along the Teesta basin."),
    ("Wayanad Landslides", "landslide", "critical", "resolved", "Wayanad, Kerala", 11.60, 76.08, 100000, "2024-07-30", "Multiple landslides caused extensive loss and infrastructure damage in Wayanad."),
    ("Delhi-NCR Flooding", "flood", "high", "resolved", "New Delhi and NCR", 28.61, 77.21, 1000000, "2023-07-13", "Yamuna flooding caused widespread inundation across low-lying areas."),
    ("Cyclone Biparjoy", "cyclone", "high", "resolved", "Kutch, Gujarat", 23.73, 69.86, 300000, "2023-06-15", "Severe cyclonic storm made landfall in coastal Gujarat."),
    ("Cyclone Tauktae", "cyclone", "high", "resolved", "Gujarat Coast", 21.64, 69.63, 5000000, "2021-05-17", "Extremely severe cyclonic storm affected western India."),
    ("Cyclone Fani", "cyclone", "critical", "resolved", "Puri, Odisha", 19.81, 85.83, 16000000, "2019-05-03", "Extremely severe cyclonic storm made landfall near Puri."),
    ("Bihar Floods", "flood", "high", "resolved", "Patna and North Bihar", 25.59, 85.14, 7000000, "2019-07-28", "Severe monsoon flooding affected multiple districts in Bihar."),
    ("Himachal Flash Floods", "flood", "high", "resolved", "Kullu, Himachal Pradesh", 31.96, 77.11, 80000, "2022-07-06", "Cloudbursts and flash floods affected Kullu and surrounding valleys."),
    ("Kerala Landslides and Floods", "landslide", "high", "resolved", "Idukki, Kerala", 9.92, 77.10, 250000, "2019-08-08", "Heavy monsoon rainfall triggered landslides and flooding across Kerala."),
    ("Cyclone Vardah", "cyclone", "high", "resolved", "Chennai, Tamil Nadu", 13.08, 80.27, 5000000, "2016-12-12", "Severe cyclonic storm made landfall near Chennai."),
]


class Command(BaseCommand):
    help = "Seed 28 historical Indian disaster incidents with their historical event dates."

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for name, dtype, severity, status, location, lat, lng, affected, date_str, description in HISTORICAL_INCIDENTS:
            occurred = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
            obj = Disaster.objects.filter(name=name, location=location).first()
            if obj:
                obj.disaster_type = dtype
                obj.severity = severity
                obj.status = status
                obj.latitude = lat
                obj.longitude = lng
                obj.affected_population = affected
                obj.description = description
                obj.created_at = occurred
                obj.updated_at = occurred
                obj.save(update_fields=[
                    "disaster_type", "severity", "status", "latitude", "longitude",
                    "affected_population", "description", "created_at", "updated_at",
                ])
                updated += 1
            else:
                obj = Disaster.objects.create(
                    name=name, disaster_type=dtype, severity=severity, status=status,
                    location=location, latitude=lat, longitude=lng,
                    affected_population=affected, description=description,
                )
                Disaster.objects.filter(pk=obj.pk).update(created_at=occurred, updated_at=occurred)
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Historical incidents ready: {created} created, {updated} updated (total {len(HISTORICAL_INCIDENTS)})."))
