from django import forms
from .models import Pago
from datetime import date


class MonthInput(forms.DateField):
    """Campo que acepta input type=month (formato YYYY-MM) y lo convierte a date día 1."""

    widget = forms.DateInput(attrs={"type": "month"})

    def strptime(self, value, format):
        from datetime import datetime

        try:
            dt = datetime.strptime(value, "%Y-%m")
            return dt.date().replace(day=1)
        except ValueError:
            raise forms.ValidationError("Ingresá un mes válido.")


class PagoEditarForm(forms.ModelForm):

    mes_cubierto = MonthInput(label="Mes que cubre")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})
        if "observaciones" in self.fields:
            self.fields["observaciones"].widget.attrs.update({"rows": 3})
        # Formatear valor inicial para type="month"
        if self.instance and self.instance.pk and self.instance.mes_cubierto:
            self.initial["mes_cubierto"] = self.instance.mes_cubierto.strftime("%Y-%m")

    class Meta:
        model = Pago
        fields = ["mes_cubierto", "monto", "observaciones"]
        widgets = {
            "monto": forms.NumberInput(attrs={"step": "0.01"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        monto = cleaned_data.get("monto")

        # Permite varios pagos parciales para el mismo mes;
        # solo se valida que el monto sea positivo.
        if monto is not None and monto <= 0:
            self.add_error("monto", "El monto debe ser mayor a cero.")

        return cleaned_data
