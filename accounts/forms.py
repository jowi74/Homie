from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth import authenticate
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    class Meta:
        model = CustomUser
        fields = ('full_name', 'username', 'email', 'password1', 'password2', 'birth_date', 'avatar')


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Usuario o correo")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'full_name', 'birth_date', 'avatar', 'is_active', 'is_staff')


# ── Formularios del Perfil ─────────────────────────────────────────────────

class UpdateUsernameForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('username',)
        labels = {'username': 'Nuevo nombre de usuario'}


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput
    )
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput,
        min_length=8
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        pwd = self.cleaned_data.get('current_password')
        if not self.user.check_password(pwd):
            raise forms.ValidationError("La contraseña actual no es correcta.")
        return pwd

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las nuevas contraseñas no coinciden.")
        return cleaned


class UpdateAvatarForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('avatar',)
        labels = {'avatar': 'Foto de perfil'}