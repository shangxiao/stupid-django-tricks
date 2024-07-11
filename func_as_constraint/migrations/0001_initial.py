from django.db import migrations
from django.db import models

import abusing_constraints.constraints


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PlaceholderModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="placeholdermodel",
            constraint=abusing_constraints.constraints.RawSQL(
                name="hello_world",
                reverse_sql="DROP FUNCTION IF EXISTS hello_world",
                sql="CREATE OR REPLACE FUNCTION hello_world()\nRETURNS varchar\nAS $$\nBEGIN\n    RETURN 'Hello World!';\nEND;\n$$ LANGUAGE plpgsql;COMMENT ON FUNCTION hello_world IS 'Print hello world!';",
            ),
        ),
    ]
