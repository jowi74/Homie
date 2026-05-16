from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from accounts.models import CustomUser
from houses.models import House
from housebedrooms.models import HouseProfile

# Solo la página index es de esta app
def index(request):
    return render(request, "index.html")

@user_passes_test(lambda u: u.is_staff)
def admin_panel(request):
    if request.method == "POST":
        action = request.POST.get('action')
        
        # ── USUARIOS ──
        if action == "give_wallet":
            username = request.POST.get('user_id')
            amount = int(request.POST.get('amount', 0))
            usr = get_object_or_404(CustomUser, username=username)
            usr.wallet_balance += amount
            usr.save()
            messages.success(request, f"Añadidos {amount} de saldo a {usr.username}.")
            
        elif action == "delete_user":
            username = request.POST.get('user_id')
            usr = get_object_or_404(CustomUser, username=username)
            if not usr.is_superuser:
                usr.delete()
                messages.success(request, f"Usuario {usr.username} eliminado correctamente.")
            else:
                messages.error(request, "No se puede eliminar a un superusuario.")
                
        elif action == "toggle_staff":
            username = request.POST.get('user_id')
            usr = get_object_or_404(CustomUser, username=username)
            usr.is_staff = not usr.is_staff
            usr.save()
            messages.success(request, f"Staff de {usr.username} cambiado a {usr.is_staff}.")
            
        elif action == "unlock_all_bedroom":
            username = request.POST.get('user_id')
            usr = get_object_or_404(CustomUser, username=username)
            # Desbloquea para todos sus perfiles en todas las casas
            profiles = HouseProfile.objects.filter(user=usr)
            for p in profiles:
                p.unlock_wallcolor = True
                p.unlock_stars_rug = True
                p.unlock_poster_gaming = True
                p.save()
            messages.success(request, f"Dormitorio desbloqueado al 100% para {usr.username} en todas sus casas.")
            
        # ── CASAS ──
        elif action == "give_house_coins":
            house_slug = request.POST.get('house_slug')
            amount = int(request.POST.get('amount', 0))
            h = get_object_or_404(House, slug=house_slug)
            h.spent_points -= amount  # spent_points negativo = puntos gratis sumados al available
            h.save()
            messages.success(request, f"Añadidos {amount} puntos comunes a la casa {h.name}.")
            
        elif action == "delete_house":
            house_slug = request.POST.get('house_slug')
            h = get_object_or_404(House, slug=house_slug)
            h.delete()
            messages.success(request, f"Casa {h.name} eliminada permanentemente.")
            
        # ── PERFILES DE CASA ──
        elif action == "give_house_points":
            profile_id = request.POST.get('profile_id')
            amount = int(request.POST.get('amount', 0))
            prof = get_object_or_404(HouseProfile, id=profile_id)
            prof.points += amount
            prof.save()
            messages.success(request, f"Añadidos {amount} pts al usuario {prof.user.username} en {prof.house.name}.")
            
        elif action == "boost_tasks":
            profile_id = request.POST.get('profile_id')
            amount = int(request.POST.get('amount', 0))
            prof = get_object_or_404(HouseProfile, id=profile_id)
            prof.completed_tasks_count += amount
            prof.save()
            messages.success(request, f"Añadidas {amount} tareas completadas al contador de {prof.user.username}.")
            
        elif action == "boost_shopping":
            profile_id = request.POST.get('profile_id')
            amount = int(request.POST.get('amount', 0))
            prof = get_object_or_404(HouseProfile, id=profile_id)
            prof.completed_shopping_count += amount
            prof.save()
            messages.success(request, f"Añadidas {amount} compras completadas al contador de {prof.user.username}.")
            
        return redirect('admin_panel')
        
    users = CustomUser.objects.all().order_by('-date_joined')
    houses = House.objects.all().order_by('-created_at')
    profiles = HouseProfile.objects.all().order_by('-points')
    
    return render(request, "admin_panel.html", {
        "usuarios": users,
        "casas": houses,
        "perfiles": profiles
    })

