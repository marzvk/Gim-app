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
        cliente = self.instance.cliente if self.instance else None
        mes_cubierto = cleaned_data.get("mes_cubierto")
        monto = cleaned_data.get("monto")

        if mes_cubierto and cliente:
            query = Pago.objects.filter(
                cliente=cliente,
                mes_cubierto__year=mes_cubierto.year,
                mes_cubierto__month=mes_cubierto.month,
            )
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                mes_nombre = mes_cubierto.strftime("%B %Y")
                self.add_error("mes_cubierto", f"Ya existe un pago para {mes_nombre}.")

        if monto is not None and monto <= 0:
            self.add_error("monto", "El monto debe ser mayor a cero.")

        return cleaned_data
