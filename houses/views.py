from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import House, HouseNote, PersonalDiaryEntry, Reminder, ChatRoom, Message
import json
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .forms import HouseForm
from accounts.utils import check_achievements

# Esto obtiene las casas del usuario logueado
@login_required
def inicio(request):
    houses = request.user.houses.all()  # casas donde el usuario es miembro
    form = HouseForm()                  # formulario vacío para el modal
    return render(request, "inicio.html", {"houses": houses, "form": form})

@login_required
def crear_casa(request):
    if request.method == "POST":
        form = HouseForm(request.POST, request.FILES)
        if form.is_valid():
            house = form.save(commit=False)
            
            # Bloquear GIF en creación ya que la casa nueva aún no los tiene desbloqueados
            if house.image and house.image.name.lower().endswith('.gif'):
                house.image = None
                
            house.creator = request.user
            house.save()
            house.members.add(request.user)  # el usuario que crea la casa
            return redirect('inicio')  # REDIRIGE a inicio en lugar de renderizar
    # Si GET o formulario inválido
    return redirect('inicio')

@login_required
def casa_detalle(request, house_slug):
    try:
        house = House.objects.get(slug=house_slug)
    except House.DoesNotExist:
        return render(request, "404.html")

    if request.user not in house.members.all():
        return redirect('inicio')

    notes = house.notes.all().order_by('-created_at')
    diary_entries = PersonalDiaryEntry.objects.filter(house=house, user=request.user).order_by('-created_at')
    
    from django.db.models import Q
    pending_reminders = Reminder.objects.filter(
        house=house
    ).exclude(read_by=request.user).filter(Q(target_user=request.user) | Q(target_user__isnull=True)| Q(creator=request.user)).order_by('trigger_time')

    return render(request, "casa.html", {
        "house": house,
        "notes": notes,
        "diary_entries": diary_entries,
        "pending_reminders": pending_reminders
    })

@login_required
def editar_nombre_casa(request, house_slug):
    try:
        house = House.objects.get(slug=house_slug)
        if request.user not in house.members.all():
            return redirect('inicio') # Solo miembros pueden editar
    except House.DoesNotExist:
        return redirect('inicio')
        
    if request.method == "POST":
        nuevo_nombre = request.POST.get('name')
        if nuevo_nombre:
            house.name = nuevo_nombre
            house.save()
    
    return redirect('inicio') # Recargar inicio para ver cambios

@login_required
def editar_foto_casa(request, house_slug):
    try:
        house = House.objects.get(slug=house_slug)
        if request.user not in house.members.all():
            return redirect('inicio')
    except House.DoesNotExist:
        return redirect('inicio')
        
    if request.method == "POST":
        nueva_foto = request.FILES.get('image')
        if nueva_foto:
            # Bloquear GIF si no está desbloqueado
            if nueva_foto.name.lower().endswith('.gif') and not house.gifs_unlocked:
                nueva_foto = None
            
            if nueva_foto:
                house.image = nueva_foto
                house.save()
            
    return redirect('inicio')

@login_required
def eliminar_miembro_casa(request, house_slug, username):
    try:
        house = House.objects.get(slug=house_slug)
        if request.user not in house.members.all():
            return redirect('inicio')
    except House.DoesNotExist:
        return redirect('inicio')
        
    if request.method == "POST":
        try:
            from accounts.models import CustomUser
            miembro = CustomUser.objects.get(username=username)
            # Remove member. If it's the last member or the creator, we might want different logic
            # but for now, just remove the user.
            house.members.remove(miembro)
            
            if house.members.count() == 0:
                house.delete() # If no members left, delete house
                
        except CustomUser.DoesNotExist:
            pass
            
    return redirect('inicio')

@login_required
def anadir_miembro_casa(request, house_slug):
    try:
        house = House.objects.get(slug=house_slug)
        if request.user not in house.members.all():
            return redirect('inicio')
    except House.DoesNotExist:
        return redirect('inicio')
        
    if request.method == "POST":
        username = request.POST.get('username')
        if username:
            try:
                from accounts.models import CustomUser
                new_member = CustomUser.objects.get(username=username)
                house.members.add(new_member)
            except CustomUser.DoesNotExist:
                pass
                
    return redirect('inicio')

from django.core.mail import send_mail
import random
import string
from django.conf import settings

@login_required
def solicitar_eliminacion_casa(request, house_slug):
    try:
        house = House.objects.get(slug=house_slug)
        if request.user != house.creator:
            return redirect('inicio')
    except House.DoesNotExist:
        return redirect('inicio')

    if request.method == "POST":
        # Generar código de 6 dígitos
        codigo = ''.join(random.choices(string.digits, k=6))
        house.deletion_code = codigo
        house.save()

        from accounts.views import send_email_async
        import threading
        
        # Enviar email en thread daemon
        threading.Thread(
            target=send_email_async,
            args=(
                f'Código de confirmación para eliminar {house.name}',
                f'Hola {request.user.username},\r\n\r\nTu código para eliminar permanentemente la casa "{house.name}" es: {codigo}\r\n\r\nSi no lo solicitaste, ignora este mensaje.',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
            ),
            daemon=True,
        ).start()
        
    return redirect('inicio')

@login_required
def confirmar_eliminacion_casa(request, house_slug):
    try:
        house = House.objects.get(slug=house_slug)
        if request.user != house.creator:
            return redirect('inicio')
    except House.DoesNotExist:
        return redirect('inicio')

    if request.method == "POST":
        import re
        codigo_raw = request.POST.get('codigo', '')
        codigo_ingresado = re.sub(r'\D', '', codigo_raw)
        print(f"DEBUG ELIMINACIÓN - Casa: {house.name} - Esperado: '{house.deletion_code}' - Ingresado: '{codigo_ingresado}'")
        if house.deletion_code and codigo_ingresado and house.deletion_code == codigo_ingresado:
            house.delete()
            from django.contrib import messages
            messages.success(request, f"La casa ha sido eliminada permanentemente.")
        else:
            from django.contrib import messages
            messages.error(request, "Código de eliminación incorrecto o expirado.")
            
    return redirect('inicio')

@login_required
def crear_nota(request, house_slug):
    if request.method == "POST":
        try:
            house = House.objects.get(slug=house_slug)
            if request.user in house.members.all():
                content = request.POST.get('content', '').strip()
                color = request.POST.get('color', '#ffffcc')
                if content:
                    HouseNote.objects.create(house=house, author=request.user, content=content, color=color)
        except House.DoesNotExist:
            pass
    return redirect('casa_detalle', house_slug=house_slug)

@login_required
def eliminar_nota(request, house_slug, note_id):
    if request.method == "POST":
        try:
            house = House.objects.get(slug=house_slug)
            note = HouseNote.objects.get(id=note_id, house=house)
            if note.author == request.user or house.creator == request.user:
                note.delete()
        except (House.DoesNotExist, HouseNote.DoesNotExist):
            pass
    return redirect('casa_detalle', house_slug=house_slug)

@login_required
def crear_entrada_diario(request, house_slug):
    if request.method == "POST":
        try:
            house = House.objects.get(slug=house_slug)
            if request.user in house.members.all():
                title = request.POST.get('title', 'Sin título').strip()
                content = request.POST.get('content', '').strip()
                if content:
                    PersonalDiaryEntry.objects.create(house=house, user=request.user, title=title, content=content)
        except House.DoesNotExist:
            pass
    return redirect('casa_detalle', house_slug=house_slug)

@login_required
def crear_recordatorio(request, house_slug):
    if request.method == "POST":
        try:
            house = House.objects.get(slug=house_slug)
            if request.user in house.members.all():
                message = request.POST.get('message', '').strip()
                trigger_time_str = request.POST.get('trigger_time')
                target_user_id = request.POST.get('target_user')
                
                if message and trigger_time_str:
                    naive_dt = parse_datetime(trigger_time_str)
                    if naive_dt:
                        import zoneinfo
                        madrid_tz = zoneinfo.ZoneInfo("Europe/Madrid")
                        trigger_time = timezone.make_aware(naive_dt, timezone=madrid_tz) if timezone.is_naive(naive_dt) else naive_dt
                        
                        target_user = None
                        if target_user_id and target_user_id != 'all':
                            target_user = house.members.filter(username=target_user_id).first()

                        Reminder.objects.create(
                            house=house, creator=request.user, message=message,
                            trigger_time=trigger_time, target_user=target_user
                        )
        except Exception as e:
            print(f"Error al crear recordatorio: {e}")
    return redirect('casa_detalle', house_slug=house_slug)

@login_required
def eliminar_recordatorio(request, house_slug, reminder_id):
    if request.method == "POST":
        try:
            house = House.objects.get(slug=house_slug)
            reminder = Reminder.objects.get(id=reminder_id, house=house)
            if reminder.creator == request.user or house.creator == request.user:
                reminder.delete()
        except (House.DoesNotExist, Reminder.DoesNotExist):
            pass
    return redirect('casa_detalle', house_slug=house_slug)

@login_required
def api_recordatorios(request, house_slug):
    try:
        house = House.objects.get(slug=house_slug)
        if request.user not in house.members.all():
            return JsonResponse({"error": "No access"}, status=403)
            
        now = timezone.now()
        from django.db.models import Q
        reminders = Reminder.objects.filter(
            house=house, trigger_time__lte=now
        ).exclude(read_by=request.user).filter(Q(target_user=request.user) | Q(target_user__isnull=True))
        
        data = []
        for r in reminders:
            data.append({
                "id": r.id,
                "message": r.message,
                "creator": r.creator.username,
                "trigger": r.trigger_time.strftime("%H:%M")
            })
            
        return JsonResponse({"reminders": data})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@login_required
def api_marcar_recordatorio_leido(request, house_slug):
    if request.method == "POST":
        try:
            house = House.objects.get(slug=house_slug)
            if request.user in house.members.all():
                body = json.loads(request.body)
                reminder_id = body.get('id')
                if reminder_id:
                    from django.db.models import Q
                    r = Reminder.objects.filter(id=reminder_id, house=house).filter(Q(target_user=request.user) | Q(target_user__isnull=True)).first()
                    if r:
                        r.read_by.add(request.user)
                        return JsonResponse({"status": "ok"})
        except Exception:
            pass
    return JsonResponse({"status": "error"}, status=400)


# ==========================================
# CHATS VIEWS
# ==========================================

@login_required
def lista_chats(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
        
    my_rooms = request.user.chat_rooms.filter(house=house)
    
    context = {
        "house": house,
        "rooms": my_rooms
    }
    return render(request, "chats.html", context)

@login_required
def crear_chat_privado(request, house_slug):
    if request.method == "POST":
        house = get_object_or_404(House, slug=house_slug)
        target_username = request.POST.get('target_user')
        if target_username:
            try:
                target_user = house.members.get(username=target_username)
                existing_rooms = ChatRoom.objects.filter(house=house, is_group=False).filter(members=request.user).filter(members=target_user)
                if existing_rooms.exists():
                    return redirect('chat_privado', house_slug=house.slug, username=target_username)
                    
                new_room = ChatRoom.objects.create(house=house, is_group=False)
                new_room.members.add(request.user, target_user)
                return redirect('chat_privado', house_slug=house.slug, username=target_username)
            except Exception:
                pass
    return redirect('lista_chats', house_slug=house_slug)

@login_required
def crear_chat_grupo(request, house_slug):
    if request.method == "POST":
        house = get_object_or_404(House, slug=house_slug)
        name = request.POST.get('name', 'Grupo sin nombre')
        members_ids = request.POST.getlist('members')
        
        if members_ids:
            img = request.FILES.get('image')
            if img and img.name.lower().endswith('.gif') and not house.gifs_unlocked:
                img = None
                
            from django.utils.text import slugify
            base_slug = slugify(name) if name else 'grupo'
            if not base_slug:
                base_slug = 'grupo'
            r_slug = base_slug
            counter = 1
            while ChatRoom.objects.filter(slug=r_slug, house=house).exists():
                r_slug = f"{base_slug}-{counter}"
                counter += 1

            new_room = ChatRoom.objects.create(house=house, name=name, slug=r_slug, is_group=True, creator=request.user, image=img)
            new_room.members.add(request.user)
            for uid in members_ids:
                try:
                    u = house.members.get(username=uid)
                    new_room.members.add(u)
                except Exception:
                    pass
            return redirect('chat_grupo', house_slug=house.slug, room_slug=new_room.slug)
    return redirect('lista_chats', house_slug=house_slug)

# --- PRIVADOS ---

@login_required
def chat_privado(request, house_slug, username):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
        
    try:
        from accounts.models import CustomUser as CU
        target_user = get_object_or_404(CU, username=username)
        room = ChatRoom.objects.filter(house=house, is_group=False).filter(members=request.user).filter(members=target_user).first()
        if not room:
            # Create silently
            room = ChatRoom.objects.create(house=house, is_group=False)
            room.members.add(request.user, target_user)
    except Exception:
        return redirect('lista_chats', house_slug=house.slug)

    other_members = room.members.exclude(id=request.user.id)
    room_name = other_members.first().username if other_members.exists() else "Solo tú"
    is_muted = room.muted_members.filter(id=request.user.id).exists()
    
    context = {
        "house": house, 
        "room": room, 
        "room_name": room_name, 
        "other_members": other_members, 
        "is_muted": is_muted,
        "is_private": True,
        "username_parameter": username
    }
    return render(request, "chat.html", context)

@login_required
def api_mensajes_chat_privado(request, house_slug, username):
    house = get_object_or_404(House, slug=house_slug)
    from accounts.models import CustomUser as CU
    target_user = CU.objects.filter(username=username).first()
    if not target_user: return JsonResponse({"deleted": True})
    room = ChatRoom.objects.filter(house=house, is_group=False).filter(members=request.user).filter(members=target_user).first()
    if not room or request.user not in room.members.all():
        return JsonResponse({"deleted": True})
        
    if request.method == "POST":
        if room.muted_members.filter(id=request.user.id).exists():
            return JsonResponse({"status": "muted"}, status=403)
        try:
            body = json.loads(request.body)
            content = body.get('content', '').strip()
            if content:
                from .models import Message
                Message.objects.create(room=room, sender=request.user, content=content)
                check_achievements(request, request.user)
                return JsonResponse({"status": "ok"})
        except Exception:
            pass
        return JsonResponse({"status": "error"}, status=400)
    else:
        last_id = int(request.GET.get('last_id', 0))
        msgs = room.messages.filter(id__gt=last_id).order_by('created_at')
        data = [{"id":m.id, "content":m.content, "sender_id":m.sender.username, "sender_name":m.sender.username, 
                 "avatar_url":m.sender.avatar.url if m.sender.avatar else "/static/img/profile_default.png",
                 "frame":m.sender.equipped_frame, "time":m.created_at.strftime("%H:%M")} for m in msgs]
        return JsonResponse({"messages": data})

@login_required
def borrar_chat_privado(request, house_slug, username):
    if request.method == "POST":
        house = get_object_or_404(House, slug=house_slug)
        from accounts.models import CustomUser as CU
        target_user = get_object_or_404(CU, username=username)
        room = ChatRoom.objects.filter(house=house, is_group=False).filter(members=request.user).filter(members=target_user).first()
        if room and request.user in room.members.all():
            room.delete()
    return redirect('lista_chats', house_slug=house_slug)

# --- GRUPOS ---

@login_required
def chat_grupo(request, house_slug, room_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
    try:
        room = ChatRoom.objects.get(slug=room_slug, house=house, is_group=True)
    except ChatRoom.DoesNotExist:
        return redirect('lista_chats', house_slug=house.slug)

    if request.user not in room.members.all():
        return redirect('lista_chats', house_slug=house.slug)
        
    other_members = room.members.exclude(id=request.user.id)
    room_name = room.name
    is_muted = room.muted_members.filter(id=request.user.id).exists()
    
    context = {"house": house, "room": room, "room_name": room_name, "other_members": other_members, "is_muted": is_muted, "is_private": False, "room_slug": room_slug}
    return render(request, "chat.html", context)
    
@login_required
def api_mensajes_chat_grupo(request, house_slug, room_slug):
    house = get_object_or_404(House, slug=house_slug)
    try:
        room = ChatRoom.objects.get(slug=room_slug, house=house, is_group=True)
    except ChatRoom.DoesNotExist:
        return JsonResponse({"deleted": True})
    if request.user not in room.members.all():
        return JsonResponse({"deleted": True})
        
    if request.method == "POST":
        if room.muted_members.filter(id=request.user.id).exists():
            return JsonResponse({"status": "muted"}, status=403)
        try:
            body = json.loads(request.body)
            content = body.get('content', '').strip()
            if content:
                from .models import Message
                Message.objects.create(room=room, sender=request.user, content=content)
                check_achievements(request, request.user)
                return JsonResponse({"status": "ok"})
        except Exception:
            pass
        return JsonResponse({"status": "error"}, status=400)
    else:
        last_id = int(request.GET.get('last_id', 0))
        msgs = room.messages.filter(id__gt=last_id).order_by('created_at')
        data = [{"id":m.id, "content":m.content, "sender_id":m.sender.username, "sender_name":m.sender.username, 
                 "avatar_url":m.sender.avatar.url if m.sender.avatar else "/static/img/profile_default.png",
                 "frame":m.sender.equipped_frame, "time":m.created_at.strftime("%H:%M")} for m in msgs]
        return JsonResponse({"messages": data})

@login_required
def chat_ajustes_grupo(request, house_slug, room_slug):
    house = get_object_or_404(House, slug=house_slug)
    try:
        room = ChatRoom.objects.get(slug=room_slug, house=house, is_group=True)
    except ChatRoom.DoesNotExist:
        return redirect('lista_chats', house_slug=house.slug)
    if request.user not in room.members.all():
        return redirect('lista_chats', house_slug=house.slug)
    
    is_creator = room.creator == request.user
    members = room.members.all()
    muted_ids = list(room.muted_members.values_list('id', flat=True))
    available_to_add = house.members.exclude(id__in=members.values_list('id', flat=True))
    
    return render(request, "chat-info-grupo.html", {
        "house": house,
        "room": room,
        "is_creator": is_creator,
        "members": members,
        "muted_ids": muted_ids,
        "available_to_add": available_to_add,
        "room_slug": room_slug
    })

@login_required
def borrar_chat_grupo(request, house_slug, room_slug):
    if request.method == "POST":
        house = get_object_or_404(House, slug=house_slug)
        room = get_object_or_404(ChatRoom, slug=room_slug, house=house, is_group=True)
        if request.user in room.members.all():
            if room.is_group and room.creator != request.user:
                pass
            else:
                room.delete()
    return redirect('lista_chats', house_slug=house_slug)

@login_required
def kick_miembro_grupo(request, house_slug, room_slug, username):
    if request.method == "POST":
        from accounts.models import CustomUser as CU
        house = get_object_or_404(House, slug=house_slug)
        room = get_object_or_404(ChatRoom, slug=room_slug, house=house, is_group=True)
        if room.creator == request.user:
            target = get_object_or_404(CU, username=username)
            room.members.remove(target)
            room.muted_members.remove(target)
    return redirect('chat_ajustes_grupo', house_slug=house_slug, room_slug=room_slug)

@login_required
def mute_miembro_grupo(request, house_slug, room_slug, username):
    if request.method == "POST":
        from accounts.models import CustomUser as CU
        house = get_object_or_404(House, slug=house_slug)
        room = get_object_or_404(ChatRoom, slug=room_slug, house=house, is_group=True)
        if room.creator == request.user:
            target = get_object_or_404(CU, username=username)
            if target in room.muted_members.all():
                room.muted_members.remove(target)
            else:
                room.muted_members.add(target)
    return redirect('chat_ajustes_grupo', house_slug=house_slug, room_slug=room_slug)

@login_required
def agregar_miembro_grupo_view(request, house_slug, room_slug):
    if request.method == "POST":
        from accounts.models import CustomUser as CU
        house = get_object_or_404(House, slug=house_slug)
        room = get_object_or_404(ChatRoom, slug=room_slug, house=house, is_group=True)
        if room.creator == request.user:
            user_ids = request.POST.getlist('new_members')
            for uid in user_ids:
                try:
                    u = house.members.get(id=uid)
                    room.members.add(u)
                except Exception:
                    pass
    return redirect('chat_ajustes_grupo', house_slug=house_slug, room_slug=room_slug)

@login_required
def cambiar_imagen_grupo_view(request, house_slug, room_slug):
    if request.method == "POST":
        house = get_object_or_404(House, slug=house_slug)
        room = get_object_or_404(ChatRoom, slug=room_slug, house=house, is_group=True)
        if room.creator == request.user:
            img = request.FILES.get('image')
            if img:
                if img.name.lower().endswith('.gif') and not house.gifs_unlocked:
                    img = None
                if img:
                    room.image = img
                    room.save()
    return redirect('chat_ajustes_grupo', house_slug=house_slug, room_slug=room_slug)

@login_required
def salir_grupo_view(request, house_slug, room_slug):
    if request.method == "POST":
        house = get_object_or_404(House, slug=house_slug)
        room = get_object_or_404(ChatRoom, slug=room_slug, house=house, is_group=True)
        if request.user in room.members.all():
            if room.creator == request.user:
                pass
            else:
                room.members.remove(request.user)
                room.muted_members.remove(request.user)
    return redirect('lista_chats', house_slug=house_slug)

@login_required
def api_chats_count(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        from django.http import JsonResponse
        return JsonResponse({"count": 0})
    count = house.chat_rooms.filter(members=request.user).count()
    from django.http import JsonResponse
    return JsonResponse({"count": count})

@login_required
def api_corcho_checksum(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    notes = house.notes.all().order_by('id')
    checksum_str = "|".join([str(n.id) for n in notes])
    return JsonResponse({'checksum': checksum_str})

@login_required
def logros(request, house_slug):
    from accounts.models import Achievement, UserAchievement
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
        
    achievements = Achievement.objects.all().order_by('target_value', 'id')
    user_unlocked_ids = set(request.user.achievements.values_list('achievement_id', flat=True))
    total_reward = sum(ach.reward_saldo for ach in achievements if ach.id in user_unlocked_ids)
    
    context = {
        "house": house,
        "achievements": achievements,
        "user_unlocked_ids": user_unlocked_ids,
        "unlocked_count": len(user_unlocked_ids),
        "total_count": achievements.count(),
        "total_reward": total_reward
    }
    return render(request, "logros.html", context)

@login_required
def finanzas(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
        
    members = house.members.all()
    expenses = house.expenses.all().order_by('-created_at')
    
    # Splitwise Math
    total_spent = sum(e.amount for e in expenses)
    members_count = members.count()
    fair_share = total_spent / members_count if members_count > 0 else 0
    
    balances = []
    from decimal import Decimal
    fair_share_dec = Decimal(str(fair_share))
    
    for member in members:
        # Lo que ha pagado originalmente él
        spent_by_member = sum(e.amount for e in expenses if e.payer == member)
        
        # Lo que ha pagado de sus deudas a otros (dinero que salió de su bolsillo)
        paid_debts = sum(Decimal(e.amount)/members_count for e in expenses if e.payer != member and member in e.paid_by.all())
        
        # Lo que otros le han devuelto a él (dinero que volvió a su bolsillo)
        received_debts = sum(Decimal(e.amount)/members_count for e in expenses if e.payer == member for p in e.paid_by.all())
        
        # Dinero efectivo neto que ha puesto para la casa
        effective_spent = spent_by_member + paid_debts - received_debts
        
        balance = effective_spent - fair_share_dec
        
        balances.append({
            'user': member,
            'spent': effective_spent,
            'balance': balance,
        })
        
    context = {
        'house': house,
        'expenses': expenses,
        'balances': balances,
        'total_spent': total_spent,
        'fair_share': fair_share_dec,
    }
    return render(request, "finanzas.html", context)

@login_required
def agregar_gasto(request, house_slug):
    if request.method == "POST":
        house = get_object_or_404(House, slug=house_slug)
        if request.user in house.members.all():
            title = request.POST.get('title', '').strip()
            amount_str = request.POST.get('amount', '0').replace(',', '.')
            try:
                from decimal import Decimal
                amount = Decimal(amount_str)
                if amount > 0 and title:
                    from .models import SharedExpense
                    SharedExpense.objects.create(
                        house=house,
                        payer=request.user,
                        title=title,
                        amount=amount
                    )
            except:
                pass
    return redirect('finanzas', house_slug=house_slug)

@login_required
def eliminar_gasto(request, house_slug, expense_id):
    if request.method == "POST":
        house = get_object_or_404(House, slug=house_slug)
        from .models import SharedExpense
        expense = get_object_or_404(SharedExpense, id=expense_id, house=house)
        # Solo el que pagó puede borrar su propio gasto
        if expense.payer == request.user:
            expense.delete()
    return redirect('finanzas', house_slug=house_slug)

@login_required
def marcar_pagado_gasto(request, house_slug, expense_id):
    if request.method == "POST":
        house = get_object_or_404(House, slug=house_slug)
        from .models import SharedExpense
        expense = get_object_or_404(SharedExpense, id=expense_id, house=house)
        # El que pagó originalmente no necesita marcarlo como pagado (ya lo pagó)
        if request.user != expense.payer:
            if request.user in expense.paid_by.all():
                expense.paid_by.remove(request.user)
            else:
                expense.paid_by.add(request.user)
    return redirect('finanzas', house_slug=house_slug)

@login_required
def api_obtener_eventos_mes(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all() and request.user != house.creator:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    month = request.GET.get('month')
    year = request.GET.get('year')
    if not month or not year:
        return JsonResponse({'events': []})
        
    from .models import HouseEvent
    events = HouseEvent.objects.filter(house=house, date__year=year, date__month=month)
    
    events_data = {}
    for event in events:
        day_str = str(event.date.day)
        if day_str not in events_data:
            events_data[day_str] = []
        events_data[day_str].append({
            'id': event.id,
            'title': event.title,
            'creator': event.creator.username,
        })
        
    return JsonResponse({'events': events_data})

@login_required
def agregar_evento_calendario(request, house_slug):
    if request.method == "POST":
        house = get_object_or_404(House, slug=house_slug)
        if request.user in house.members.all() or request.user == house.creator:
            title = request.POST.get('title', '').strip()
            date_str = request.POST.get('date', '') # formato YYYY-MM-DD
            if title and date_str:
                from datetime import datetime
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    from .models import HouseEvent
                    HouseEvent.objects.create(
                        house=house,
                        creator=request.user,
                        title=title,
                        date=date_obj
                    )
                    print("Event created successfully:", title, date_str)
                except Exception as e:
                    print("Error creating event:", e, "title:", title, "date:", date_str)
            else:
                print("Missing title or date_str:", title, date_str)
    return redirect('casa_detalle', house_slug=house_slug)

@login_required
def eliminar_evento_calendario(request, house_slug, event_id):
    if request.method == "POST":
        house = get_object_or_404(House, slug=house_slug)
        from .models import HouseEvent
        event = get_object_or_404(HouseEvent, id=event_id, house=house)
        # Solo el creador puede eliminar su evento
        if event.creator == request.user:
            event.delete()
    return JsonResponse({'ok': True})
