from uuid import uuid4

from django.db import migrations, models
import crm.models


def fill_quote_tokens(apps, schema_editor):
    Quotation = apps.get_model("crm", "Quotation")
    for quote in Quotation.objects.filter(share_token__isnull=True).iterator():
        quote.share_token = uuid4()
        quote.save(update_fields=["share_token"])


class Migration(migrations.Migration):
    dependencies = [("crm", "0002_seed_service_plans")]

    operations = [
        migrations.AddField(
            model_name="serviceteammember",
            name="user",
            field=models.OneToOneField(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="service_profile", to="crm.user"),
        ),
        migrations.AddField(
            model_name="quotation",
            name="share_token",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.RunPython(fill_quote_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="quotation",
            name="share_token",
            field=models.UUIDField(default=crm.models.quotation_share_token, editable=False, unique=True),
        ),
    ]
