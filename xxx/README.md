Read from view, write to table
==============================

Feb 2026


Notes
-----

A couple of different strategies:

Stategry 1: Route to the view or table depending on the operation
 - The queryset can initialise an "initial join" to the view preemptively before the base table which
   gives you basic queryset usage
   - Use annotations for the calculated fields
 - objects.create() remains ok
 - save() ok
 - problem with objects.update(), need to revert this with qs.query.change_aliases() being careful
   not to reorder the aliases for querysets with multiple (in the case of joins etc) so that a different
   table becomes the initial alias
 - For deferred attributes/refresh_from_db():
   - change the annotations to a new type of field like GeneratedField but simpler
   - set the base manager to the one defined above
 - doing a select_related() from a related model is still a problem


Strategy 2: Model backed by view with triggers for create/update/delete
 - Problem then becomes migrations
