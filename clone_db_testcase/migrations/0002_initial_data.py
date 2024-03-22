from django.db import migrations


def initial_data(apps, schema_editor):
    DomainWhitelist = apps.get_model("clone_db_testcase", "DomainWhitelist")
    DomainWhitelist.objects.create(domain="djangoproject.com")


class Migration(migrations.Migration):
    dependencies = [
        ("clone_db_testcase", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            code=initial_data, reverse_code=migrations.RunPython.noop, elidable=False
        )
    ]
