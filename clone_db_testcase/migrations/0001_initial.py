from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DomainWhitelist",
            fields=[
                (
                    "domain",
                    models.CharField(primary_key=True, max_length=255, serialize=False),
                ),
            ],
        ),
    ]
