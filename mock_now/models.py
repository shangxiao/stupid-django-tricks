from django.db import models

create_view = """\
CREATE OR REPLACE VIEW now_view AS
SELECT now()
"""

drop_view = """\
DROP VIEW IF EXISTS now_view
"""


class Now(models.Model):
    now = models.DateTimeField(primary_key=True)

    class Meta:
        db_table = "now_view"
        managed = False
