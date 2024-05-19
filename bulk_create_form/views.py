from django.forms import BaseModelFormSet
from django.forms import modelformset_factory
from django.shortcuts import render

from .models import User


class BaseUserFormSet(BaseModelFormSet):
    # modelformset_factory() unfortunately has no way to set queryset & prevent loading from the db
    def get_queryset(self):
        return User.objects.none()


def bulk_create_users(request):
    UserFormSet = modelformset_factory(
        model=User,
        formset=BaseUserFormSet,
        fields="__all__",
        min_num=1,
        extra=0,
    )

    if request.method == "POST" and "add-row" in request.POST:
        # extra is zero-based, so extra = current total since total = min_num + extra
        UserFormSet.extra = int(request.POST["form-TOTAL_FORMS"])
        # preserve user input without binding the form by loading it as initial
        initial = [
            {
                field_name: request.POST.get(f"form-{i}-{field_name}")
                for field_name in UserFormSet.form.base_fields
            }
            for i in range(int(request.POST["form-TOTAL_FORMS"]))
        ]
        formset = UserFormSet(initial=initial)

    elif request.method == "POST":
        formset = UserFormSet(data=request.POST)

        num_populated_forms = sum(
            filter(
                None,
                (
                    all(
                        request.POST.get(f"form-{i}-{field_name}", "") != ""
                        for field_name in UserFormSet.form.base_fields
                    )
                    for i in range(int(request.POST["form-TOTAL_FORMS"]))
                ),
            )
        )
        if num_populated_forms >= 1:
            for form in formset:
                form.empty_permitted = True

        if formset.is_valid():
            formset.save()
            users = [form.instance for form in formset.forms]
            return render(request, "bulk_create_form/success.html", {"users": users})
    else:
        formset = UserFormSet()

    return render(request, "bulk_create_form/bulk_create.html", {"formset": formset})


def bulk_create_users_js(request):
    UserFormSet = modelformset_factory(
        model=User,
        formset=BaseUserFormSet,
        fields="__all__",
        min_num=1,
        extra=0,
    )
    if request.method == "POST":
        formset = UserFormSet(data=request.POST)
        if formset.is_valid():
            formset.save()
            users = [form.instance for form in formset.forms]
            return render(request, "bulk_create_form/success.html", {"users": users})
    else:
        formset = UserFormSet()
    return render(request, "bulk_create_form/bulk_create_js.html", {"formset": formset})
