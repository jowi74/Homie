from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from houses.models import House
from accounts.models import CustomUser
from .models import HouseProfile, WALL_COLORS

@login_required
def lista_dormitorios(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
        
    for member in house.members.all():
        HouseProfile.objects.get_or_create(user=member, house=house)
        
    profiles = HouseProfile.objects.filter(house=house).order_by('-points')
    my_profile = profiles.filter(user=request.user).first()
    other_profiles = list(profiles.exclude(user=request.user))
    active_member_ids = set(house.members.values_list('id', flat=True))
    
    from .models import PrivateNickname
    my_nicknames_qs = PrivateNickname.objects.filter(owner=request.user, house=house)
    my_nicknames = { nn.target_user.id: nn.nickname for nn in my_nicknames_qs }
    
    for p in other_profiles:
        p.nickname = my_nicknames.get(p.user.id)
        p.is_active_member = p.user.id in active_member_ids
    
    context = {
        "house": house,
        "my_profile": my_profile,
        "other_profiles": other_profiles
    }
    return render(request, "dormitorios.html", context)

@login_required
def ver_dormitorio(request, house_slug, username):
    import logging, traceback
    logger = logging.getLogger(__name__)
    try:
        house = get_object_or_404(House, slug=house_slug)
        if request.user not in house.members.all():
            return redirect('inicio')
            
        target_user = get_object_or_404(CustomUser, username=username)
        if target_user not in house.members.all():
            return redirect('lista_dormitorios', house_slug=house.slug)
            
        profile, created = HouseProfile.objects.get_or_create(user=target_user, house=house)
        
        from .models import PrivateNickname
        nn = PrivateNickname.objects.filter(owner=request.user, target_user=target_user, house=house).first()
        if nn:
            profile.nickname = nn.nickname
        
        is_owner = (request.user == target_user)
        
        context = {
            "house": house,
            "target_user": target_user,
            "profile": profile,
            "is_owner": is_owner,
            "wall_colors": WALL_COLORS,
        }
        return render(request, "dormitorio.html", context)
    except Exception as e:
        logger.error(f"ERROR en ver_dormitorio house={house_slug} user={username}: {e}\n{traceback.format_exc()}")
        raise

@login_required
def guardar_estilo_dormitorio(request, house_slug, username):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
    if request.user.username != username:
        return redirect('ver_dormitorio', house_slug=house_slug, username=username)
    
    if request.method == "POST":
        profile, _ = HouseProfile.objects.get_or_create(user=request.user, house=house)
        
        wall = request.POST.get('wallcolor', '').strip()
        VALID_WALLS = [c[0] for c in WALL_COLORS]
        if wall in VALID_WALLS and profile.unlock_wallcolor:
            profile.bedroom_wallcolor = wall
        
        rug = request.POST.get('rug_style', '').strip()
        if rug == 'rug_stars' and profile.unlock_stars_rug:
            profile.bedroom_rug_style = 'rug_stars'
        elif rug == 'rug_default':
            profile.bedroom_rug_style = 'rug_default'
        
        poster = request.POST.get('poster', '').strip()
        if poster == 'poster_gaming' and profile.unlock_poster_gaming:
            profile.bedroom_poster = 'poster_gaming'
        elif poster == 'none':
            profile.bedroom_poster = 'none'
        
        profile.save()
    
    return redirect('ver_dormitorio', house_slug=house_slug, username=username)



@login_required
def ranking(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
        
    profiles = list(HouseProfile.objects.filter(house=house))
    
    from .models import PrivateNickname
    my_nicknames_qs = PrivateNickname.objects.filter(owner=request.user, house=house)
    my_nicknames = { nn.target_user.id: nn.nickname for nn in my_nicknames_qs }
    
    for p in profiles:
        if p.user != request.user:
            p.nickname = my_nicknames.get(p.user.id)
            
    profiles_points = sorted(profiles, key=lambda x: x.points, reverse=True)[:5]
    profiles_tasks = sorted(profiles, key=lambda x: x.completed_tasks_count, reverse=True)[:5]
    profiles_shopping = sorted(profiles, key=lambda x: x.completed_shopping_count, reverse=True)[:5]
            
    from django.db.models import Sum, F
    houses_qs = House.objects.annotate(
        total_p=Sum('house_profiles__points', default=0),
        total_t=Sum('house_profiles__completed_tasks_count', default=0),
        total_s=Sum('house_profiles__completed_shopping_count', default=0)
    ).annotate(
        total_actions=F('total_t') + F('total_s')
    )
    
    global_points = houses_qs.order_by('-total_p')[:5]
    global_actions = houses_qs.order_by('-total_actions')[:5]

    return render(request, "ranking.html", {
        "house": house, 
        "profiles_points": profiles_points,
        "profiles_tasks": profiles_tasks,
        "profiles_shopping": profiles_shopping,
        "global_points": global_points,
        "global_actions": global_actions
    })

@login_required
def eliminar_dormitorio(request, house_slug, username):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all() and request.user != house.creator:
        return redirect('inicio')
        
    if request.method == "POST":
        target_user = get_object_or_404(CustomUser, username=username)
        HouseProfile.objects.filter(user=target_user, house=house).delete()
    return redirect('lista_dormitorios', house_slug=house.slug)

@login_required
def poner_mote(request, house_slug, username):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
        
    if request.method == "POST":
        target_user = get_object_or_404(CustomUser, username=username)
        nuevo_mote = request.POST.get('nickname', '').strip()
        
        from .models import PrivateNickname
        if nuevo_mote:
            nn, _ = PrivateNickname.objects.get_or_create(
                owner=request.user, target_user=target_user, house=house,
                defaults={'nickname': nuevo_mote}
            )
            nn.nickname = nuevo_mote
            nn.save()
        else:
            PrivateNickname.objects.filter(owner=request.user, target_user=target_user, house=house).delete()
            
    return redirect('lista_dormitorios', house_slug=house.slug)
