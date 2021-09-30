Implicit Parent-Child Relationships via Nested Models
=====================================================

Take advantage of Python class nesting to define existentially-dependent parent-child relationships!

Given the following model definition:

```python
class Parent(models.Model):

    class Child(models.Model):
        ...
```

By applying the metaclass patch, the model `Parent.Child` will gain a not null, cascading, foreign key to `Parent`:

```python
> Parent.Child._meta.get_fields()
(<django.db.models.fields.BigAutoField: id>,
 <django.db.models.fields.related.ForeignKey: parent>)

> Parent.Child._meta.get_field('parent').null
False

> parent = Parent.objects.create()

> child = Parent.Child.objects.create(parent=parent)

> child.parent
<Parent: Parent object (1)>

> parent.delete()
(2, {'nested_models.Child': 1, 'nested_models.Parent': 1})

> child.refresh_from_db()
---------------------------------------------------------------------------
 ... <traceback omitted> ...

DoesNotExist: Child matching query does not exist.
```
