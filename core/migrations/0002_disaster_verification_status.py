from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="disaster",
            name="verification_status",
            field=models.CharField(
                choices=[
                    ("unverified", "Unverified"),
                    ("confirmed", "Confirmed"),
                    ("corrected", "Corrected"),
                    ("rejected", "Rejected"),
                ],
                default="unverified",
                max_length=12,
            ),
        ),
    ]