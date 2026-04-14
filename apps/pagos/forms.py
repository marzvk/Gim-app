from django import forms
from .models import Pago


class PagoEditarForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ["monto", "observaciones"]
        widgets = {
            "monto": forms.NumberInput(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
