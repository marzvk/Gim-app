from django import forms
from .models import Cliente, Plan
from apps.usuarios.models import Turno


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ["codigo", "nombre", "precio", "activo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # El código es único e identifica al plan en backups/imports: solo al crear.
        if self.instance and self.instance.pk:
            self.fields.pop("codigo", None)

        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.update({"class": "form-select"})
            else:
                field.widget.attrs.update({"class": "form-control"})


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "apellido", "plan", "turno", "telefono", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            # Si el campo es de selección (ChoiceField), usa form-select, sino form-control
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.update({"class": "form-select"})
            else:
                field.widget.attrs.update({"class": "form-control"})
