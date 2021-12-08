Custom SQL Backed Django Models
===============================

This example shows how you can create Django models backed by custom SQL.

Here we have a model that is backed by
[PostgreSQL's set returning function `generate_series()`](https://www.postgresql.org/docs/current/functions-srf.html)
to produce either an integer or date(time) series.

Integer series from 0 to 10 with an interval of 2:

```python
> GenerateIntegerSeries.objects.all(0, 10, 2).values_list('series', flat=True)
<QuerySet [0, 2, 4, 6, 8, 10]>
```

Date series from 1st Jan 2021 to 31st Dec 2021 with an interval of 1 month:

```python
> from datetime import date
> GenerateDateSeries.objects.all(date(2021, 1, 1), date(2021, 12, 31), '1 month').values_list('date', flat=True)
<QuerySet [
    datetime.date(2021, 1, 1),
    datetime.date(2021, 2, 1),
    datetime.date(2021, 3, 1),
    datetime.date(2021, 4, 1),
    datetime.date(2021, 5, 1),
    datetime.date(2021, 6, 1),
    datetime.date(2021, 7, 1),
    datetime.date(2021, 8, 1),
    datetime.date(2021, 9, 1),
    datetime.date(2021, 10, 1),
    datetime.date(2021, 11, 1),
    datetime.date(2021, 12, 1)]>
```

Datetime series on 1st Jan 2021 from 9:00am to 5:00pm with an interval of 1 hour:

```python
> from datetime import datetime
> GenerateDateTimeSeries.objects.all(datetime(2021, 1, 1, 9, 0, 0), datetime(2021, 1, 1, 17, 0, 0), '1 hour').values_list('timestamp', flat=True)
<QuerySet [
    datetime.datetime(2021, 1, 1, 9, 0),
    datetime.datetime(2021, 1, 1, 10, 0),
    datetime.datetime(2021, 1, 1, 11, 0),
    datetime.datetime(2021, 1, 1, 12, 0),
    datetime.datetime(2021, 1, 1, 13, 0),
    datetime.datetime(2021, 1, 1, 14, 0),
    datetime.datetime(2021, 1, 1, 15, 0),
    datetime.datetime(2021, 1, 1, 16, 0),
    datetime.datetime(2021, 1, 1, 17, 0)]>
```
