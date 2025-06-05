import abusing_constraints.constraints
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("bitemporal", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="account",
            constraint=abusing_constraints.constraints.RawSQL(
                name="account_update_function",
                reverse_sql="# DROP FUNCTION IF EXISTS account_update_function;\n",
                sql="CREATE OR REPLACE FUNCTION account_update_function()\nRETURNS trigger AS $$\nBEGIN\n    -- Insert new entry with updated values\n    INSERT INTO bitemporal_account (name, address) VALUES (NEW.name, NEW.address);\n\n    -- Prevent the original update by using OLD with only updated valid_time\n    OLD.valid_time := tstzrange(lower(OLD.valid_time), now());\n    RETURN OLD;\nEND;\n$$ LANGUAGE plpgsql;\n",
            ),
        ),
        migrations.AddConstraint(
            model_name="account",
            constraint=abusing_constraints.constraints.RawSQL(
                name="account_update_trigger",
                reverse_sql="DROP TRIGGER IF EXISTS account_update_trigger ON bitemporal_account;\n",
                sql="CREATE TRIGGER account_update_trigger\nBEFORE UPDATE ON bitemporal_account\nFOR EACH ROW\nEXECUTE FUNCTION account_update_function();\n",
            ),
        ),
    ]
