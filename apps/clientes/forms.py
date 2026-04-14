from django import forms
from .models import Cliente, Plan
from apps.usuarios.models import Turno


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "apellido", "plan", "turno", "telefono", "email"]
        widgets = {
            field: forms.TextInput(attrs={"class": "form-control"})
            for field in ["nombre", "apellido", "telefono", "email"]
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Clases de Bootstrap para los Selects
        self.fields["plan"].widget.attrs.update({"class": "form-select"})
        self.fields["turno"].widget.attrs.update({"class": "form-select"})
