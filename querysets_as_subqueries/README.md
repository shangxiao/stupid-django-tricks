Querysets as Subqueries
=======================

Draft

August 2023

Forcing subqueries.



Approach 1
----------

 - Use a clean unregistered model
 - Either:
   - add a `row_number()` annotation to satisfy the default pk every model gets; or
   - fudge the meta to remove the pk however this is sketchy; eg redefining `concrete_fields = []` isn't enough
     other attributes may require updating like `queryset.query.default_cols = False` ?
 - Add all annotations & selects as new annotations on the new queryset


Approach 2
----------

 - Dynamically define new unregistered model with all annotations & selects as attributes
