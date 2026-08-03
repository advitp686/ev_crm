from django.db import migrations


def seed_service_plans(apps, schema_editor):
    ServicePlan = apps.get_model("crm", "ServicePlan")
    plans = ((1, 500), (2, 1500), (3, 3500))
    for sequence, km in plans:
        ServicePlan.objects.get_or_create(
            sequence=sequence,
            defaults={
                "name": f"Free Service {sequence} - {km:,} km",
                "due_km": km,
                "is_free": True,
                "price": 0,
                "is_active": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("crm", "0001_initial")]
    operations = [migrations.RunPython(seed_service_plans, migrations.RunPython.noop)]
