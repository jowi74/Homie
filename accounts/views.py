import random
import threading
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import CustomUser

def send_email_async(subject, message, from_email, recipient_list):
    """Envía un correo via Brevo HTTP API (sin SMTP) en un thread separado."""
    import os, json, urllib.request, urllib.error

    api_key = os.environ.get('BREVO_API_KEY', '')

    if api_key:
        # Usar Brevo API (HTTP) — funciona en Render free tier
        try:
            sender_email = os.environ.get('BREVO_FROM_EMAIL', from_email)
            sender_name = os.environ.get('BREVO_FROM_NAME', 'Homie')
            payload = {
                "sender": {"name": sender_name, "email": sender_email},
                "to": [{"email": r} for r in recipient_list],
                "subject": subject,
                "textContent": message,
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                'https://api.brevo.com/v3/smtp/email',
                data=data,
                headers={
                    'api-key': api_key,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                print(f"[EMAIL] ✅ Brevo: {resp.status} enviado a {recipient_list}")
        except Exception as e:
            print(f"[EMAIL] ❌ Error Brevo: {type(e).__name__}: {e}")
    else:
        # Fallback: SMTP de Django (solo funciona en desarrollo local)
        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            print(f"[EMAIL] ✅ SMTP enviado a {recipient_list}")
        except Exception as e:
            print(f"[EMAIL] ❌ Error SMTP: {type(e).__name__}: {e}")


def generar_codigo():
    return str(random.randint(100000, 999999))

def register_view(request):
    # Borrado automático de cuentas abandonadas en estado inactivo tras 60 segundos
    tiempo_limite = timezone.now() - timedelta(seconds=60)
    CustomUser.objects.filter(is_active=False, date_joined__lt=tiempo_limite).delete()
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)

        if form.is_valid():
            email = form.cleaned_data["email"]

            if CustomUser.objects.filter(email=email, is_active=True).exists():
                return render(request, "registro.html", {
                    "form": form,
                    "error": "Ya existe una cuenta con ese correo electrónico.",
                })

            CustomUser.objects.filter(email=email, is_active=False).delete()

            # Crear usuario inactivo
            user = form.save(commit=False)
            user.is_active = False
            full_name = form.cleaned_data.get("full_name", "")
            name_parts = full_name.split()
            user.first_name = name_parts[0] if name_parts else ""
            user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            user.save()

            codigo = generar_codigo()
            print(f">>>>> [MODO DEV] CÓDIGO OTP PARA {email}: {codigo} <<<<<")
            
            # Solo guardamos el email y el código en sesión
            request.session['reg_email'] = email
            request.session['reg_code'] = codigo

            # Disparar el correo en un thread daemon — así gunicorn no espera ni muere
            username = user.username
            t = threading.Thread(
                target=send_email_async,
                args=(
                    "Tu código de verificación de Homie",
                    (
                        f"¡Hola {username}!\n\n"
                        f"Tu código de verificación es: {codigo}\n\n"
                        f"Introdúcelo en la pantalla de registro para completar tu cuenta.\n\n"
                        f"— El equipo de Homie"
                    ),
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                ),
                daemon=True,
            )
            t.start()

            return redirect("verify_email")

    else:
        form = CustomUserCreationForm()

    return render(request, "registro.html", {"form": form})


def verify_email_view(request):
    if 'reg_email' not in request.session or 'reg_code' not in request.session:
        return redirect('register')
        
    error = None
    email = request.session['reg_email']
    
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == "verify":
            codigo_input = request.POST.get('code', '').strip()
            if codigo_input == request.session['reg_code']:
                # Buscar el usuario inactivo por email
                try:
                    user = CustomUser.objects.get(email=email, is_active=False)
                    user.is_active = True
                    user.save()
                    
                    # Limpiar sesión
                    del request.session['reg_email']
                    del request.session['reg_code']
                    
                    # Logear y mandar al inicio
                    # Como hay múltiples backends configurados en settings, especificamos el estándar a mano
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)
                    return redirect('inicio')
                except CustomUser.DoesNotExist:
                    error = "Cuenta no encontrada o ya está activa."
            else:
                error = "El código es incorrecto. Por favor, inténtalo de nuevo."
                
        elif action == "resend":
            nuevo_codigo = generar_codigo()
            request.session['reg_code'] = nuevo_codigo
            try:
                # Opcional: Obtener username si lo necesitamos para el correo
                user = CustomUser.objects.get(email=email, is_active=False)
                username = user.username
            except:
                username = "Usuario"

            print(f">>>>> [MODO DEV REENVÍO] CÓDIGO OTP PARA {email}: {nuevo_codigo} <<<<<")
            threading.Thread(
                target=send_email_async,
                args=(
                    "Nuevo código de verificación - Homie",
                    (
                        f"¡Hola {username}!\n\n"
                        f"Acabas de solicitar un nuevo código. Tu nuevo código de verificación es: {nuevo_codigo}\n\n"
                        f"— El equipo de Homie"
                    ),
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                ),
                daemon=True,
            ).start()
            error = "¡Nuevo código enviado! Revisa tu bandeja (y el spam)."

    return render(request, "verificar_email.html", {"email": email, "error": error})

def login_view(request):
    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("inicio")
    else:
        form = CustomAuthenticationForm()

    return render(request, "login.html", {"form": form})


@login_required
def profile_view(request):
    from .forms import UpdateUsernameForm, ChangePasswordForm, UpdateAvatarForm
    from django.contrib.auth import update_session_auth_hash

    user = request.user
    success = None
    error = None

    username_form = UpdateUsernameForm(instance=user)
    password_form = ChangePasswordForm(user=user)
    avatar_form = UpdateAvatarForm(instance=user)

    if request.method == "POST":
        action = request.POST.get("action")

        # ── Cambiar nombre de usuario ──────────────────────────────────────
        if action == "update_username":
            username_form = UpdateUsernameForm(request.POST, instance=user)
            if username_form.is_valid():
                username_form.save()
                success = "Nombre de usuario actualizado correctamente."
            else:
                error = username_form.errors.as_text()

        # ── Cambiar contraseña ─────────────────────────────────────────────
        elif action == "change_password":
            password_form = ChangePasswordForm(user=user, data=request.POST)
            if password_form.is_valid():
                user.set_password(password_form.cleaned_data["new_password1"])
                user.save()
                update_session_auth_hash(request, user)  # mantiene la sesión activa
                success = "Contraseña cambiada correctamente."
            else:
                error = password_form.errors.as_text()

        # ── Cambiar avatar ─────────────────────────────────────────────────
        elif action == "update_avatar":
            avatar_file = request.FILES.get('avatar')
            if avatar_file and avatar_file.name.lower().endswith('.gif') and not user.gifs_unlocked:
                error = "¡Los GIFs animados en el perfil son Premium! Desbloquéalo en la Tienda."
            else:
                avatar_form = UpdateAvatarForm(request.POST, request.FILES, instance=user)
                if avatar_form.is_valid():
                    try:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"[HOMIE] Subiendo avatar para {user.username}...")
                        avatar_form.save()
                        logger.info(f"[HOMIE] Avatar guardado: {user.avatar}")
                        success = "Foto de perfil actualizada."
                    except Exception as e:
                        import traceback
                        logging.getLogger(__name__).error(f"[HOMIE] ERROR al subir avatar: {e}\n{traceback.format_exc()}")
                        error = f"Error al subir: {str(e)}"
                else:
                    error = "Error al subir la imagen."

        # ── Convertir Tareas y Compras en Saldo ────────────────────────────
        elif action == "convert_points":
            total_tasks_user = sum(p.completed_tasks_count for p in user.house_profiles.all())
            total_shopping_user = sum(p.completed_shopping_count for p in user.house_profiles.all())
            
            if total_tasks_user >= 25 and total_shopping_user >= 25:
                # Restar 25 tareas
                tasks_to_remove = 25
                for p in user.house_profiles.all():
                    if tasks_to_remove > 0 and p.completed_tasks_count > 0:
                        rem = min(tasks_to_remove, p.completed_tasks_count)
                        p.completed_tasks_count -= rem
                        tasks_to_remove -= rem
                        p.save()
                
                # Restar 25 compras
                shopping_to_remove = 25
                for p in user.house_profiles.all():
                    if shopping_to_remove > 0 and p.completed_shopping_count > 0:
                        rem = min(shopping_to_remove, p.completed_shopping_count)
                        p.completed_shopping_count -= rem
                        shopping_to_remove -= rem
                        p.save()
                
                user.wallet_balance += 100
                user.save()
                success = "¡Has canjeado 25 tareas y 25 compras por 100 monedas!"
            else:
                error = "Necesitas al menos 25 tareas y 25 compras completadas para canjear."

        elif action == "equip_frame":
            frame_name = request.POST.get('frame_name', '')
            from .models import UserFrame
            if frame_name and user.frames.filter(frame_name=frame_name).exists():
                user.equipped_frame = frame_name
                user.save()
                success = "Marco equipado correctamente."
            elif frame_name == "__none__":
                user.equipped_frame = None
                user.save()
                success = "Marco removido."

    # ── Estadísticas ───────────────────────────────────────────────────────
    from housetasks.models import Task
    from shopping.models import ShoppingItem
    from .models import UserFrame

    total_tasks = sum(p.completed_tasks_count for p in user.house_profiles.all())
    user_houses = user.houses.all()
    total_shopping = sum(p.completed_shopping_count for p in user.house_profiles.all())
    owned_frames = user.frames.all()

    return render(request, "profile.html", {
        "username_form": username_form,
        "password_form": password_form,
        "avatar_form": avatar_form,
        "success": success,
        "error": error,
        "total_tasks": total_tasks,
        "total_shopping": total_shopping,
        "owned_frames": owned_frames,
    })

def forgot_password_view(request):
    error = None
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if email:
            try:
                user = CustomUser.objects.get(email=email, is_active=True)
                codigo = generar_codigo()
                request.session['reset_email'] = email
                request.session['reset_code'] = codigo
                
                print(f">>>>> [MODO DEV] CÓDIGO OTP RECUPERACIÓN PARA {email}: {codigo} <<<<<")
                
                username = user.username
                threading.Thread(
                    target=send_email_async,
                    args=(
                        "Restablecer tu contraseña en Homie",
                        (
                            f"¡Hola {username}!\n\n"
                            f"Has solicitado restablecer tu contraseña.\n"
                            f"Tu código de seguridad es: {codigo}\n\n"
                            f"Introdúcelo en la web para crear una nueva contraseña. Si no fuiste tú, ignora este mensaje.\n\n"
                            f"— El equipo de Homie"
                        ),
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                    ),
                    daemon=True,
                ).start()
                    
                return redirect("reset_password")
            except CustomUser.DoesNotExist:
                error = "No existe ninguna cuenta activa asociada a este correo."
        else:
            error = "Por favor, introduce tu correo electrónico."
            
    return render(request, "olvido_password.html", {"error": error})

def reset_password_view(request):
    if 'reset_email' not in request.session or 'reset_code' not in request.session:
        return redirect('login')
        
    error = None
    email = request.session['reset_email']
    
    if request.method == "POST":
        codigo_input = request.POST.get('code', '').strip()
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if codigo_input != request.session['reset_code']:
            error = "El código es incorrecto."
        elif not new_password or not confirm_password:
            error = "Por favor, rellena ambos campos de contraseña."
        elif new_password != confirm_password:
            error = "Las contraseñas no coinciden. Inténtalo de nuevo."
        elif len(new_password) < 4:
            error = "La contraseña debe tener al menos 4 caracteres."
        else:
            try:
                user = CustomUser.objects.get(email=email, is_active=True)
                user.set_password(new_password)
                user.save()
                
                # Limpiar sesión
                del request.session['reset_email']
                del request.session['reset_code']
                
                return redirect('login')
            except CustomUser.DoesNotExist:
                error = "Error crítico: El usuario ya no existe o está inactivo."
                
    return render(request, "restablecer_password.html", {"email": email, "error": error})


@login_required
def delete_account_view(request):
    error = None
    email = request.user.email
    
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == "send_code":
            codigo = generar_codigo()
            print(f">>>>> [MODO DEV - BORRADO CUENTA] CÓDIGO OTP PARA {email}: {codigo} <<<<<")
            
            request.session['del_code'] = codigo
            
            username = request.user.username
            t = threading.Thread(
                target=send_email_async,
                args=(
                    "Tu código para eliminar tu cuenta en Homie",
                    (
                        f"¡Hola {username}!\n\n"
                        f"Has solicitado eliminar tu cuenta de forma permanente.\n\n"
                        f"Tu código de confirmación es: {codigo}\n\n"
                        f"Si no has sido tú, cambia tu contraseña inmediatamente.\n\n"
                        f"— El equipo de Homie"
                    ),
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                ),
                daemon=True,
            )
            t.start()
            
            return render(request, "verificar_borrado_cuenta.html", {"email": email, "step": "verify"})
            
        elif action == "verify_code":
            codigo_input = request.POST.get('code', '').strip()
            
            if 'del_code' in request.session and codigo_input == request.session['del_code']:
                # Borrar usuario
                user = request.user
                del request.session['del_code']
                user.delete()
                
                # Al borrarlo, se desloguea automáticamente, pero por si acaso podríamos redirigir al inicio 
                return redirect('index')
            else:
                error = "El código es incorrecto. Por favor, inténtalo de nuevo."
                return render(request, "verificar_borrado_cuenta.html", {"email": email, "step": "verify", "error": error})

    return redirect('profile')