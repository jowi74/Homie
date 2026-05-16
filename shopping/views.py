from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from houses.models import House
from .models import ShoppingItem
from housebedrooms.models import HouseProfile
from accounts.utils import check_achievements

@login_required
def lista_compra(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
        
    items = house.shopping_items.all().order_by('created_at')
    
    if request.method == "POST":
        
        name = request.POST.get('name')
        quantity = request.POST.get('quantity', '').strip()
        if name:
            ShoppingItem.objects.create(house=house, name=name, quantity=quantity or None)
            return redirect('lista_compra', house_slug=house.slug)
            
    return render(request, "compra.html", {"house": house, "items": items})

@login_required
def eliminar_item(request, house_slug, item_id):
    house = get_object_or_404(House, slug=house_slug)
    if request.user in house.members.all():
        item = get_object_or_404(ShoppingItem, id=item_id, house=house)
        item.delete()
    return redirect('lista_compra', house_slug=house.slug)

@login_required
def completar_compra(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user in house.members.all():
        if house.shopping_items.exists():
            profile, _ = HouseProfile.objects.get_or_create(user=request.user, house=house)
            items_count = house.shopping_items.count()
            profile.points += 30
            profile.completed_shopping_count += items_count
            profile.save()
            house.shopping_items.all().delete()
            check_achievements(request, request.user)
    return redirect('lista_compra', house_slug=house.slug)

@login_required
def tienda(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
        
    profile, _ = HouseProfile.objects.get_or_create(user=request.user, house=house)
    
    if request.method == "POST":
        from .models import Purchase
        action = request.POST.get('action')
        
        if action == "buy_house_gifs":
            if house.available_points >= 300 and not house.gifs_unlocked:
                house.spent_points += 300
                house.gifs_unlocked = True
                house.save()
                Purchase.objects.create(house=house, buyer=request.user, item_name="🎉 GIFs para la Casa", currency_type='puntos', amount=300)
                
        elif action == "buy_personal_gifs":
            if request.user.wallet_balance >= 100 and not request.user.gifs_unlocked:
                request.user.wallet_balance -= 100
                request.user.gifs_unlocked = True
                request.user.save()
                Purchase.objects.create(house=house, buyer=request.user, item_name="🎉 GIFs Personales", currency_type='saldo', amount=100)

        elif action == "buy_frame":
            from accounts.models import UserFrame
            frame_name = request.POST.get('frame_name', '')
            VALID_FRAMES = [
                'marco1.png', 'marco3.png',
                'marcoNeon1.png', 'marcoNeon2.png', 'marcoNeon3.png',
                'marcoNeon4.png', 'marcoNeon5.png',
            ]
            FRAME_LABELS = {
                'marco1.png': 'Marco Dorado', 'marco3.png': 'Marco Elegante',
                'marcoNeon1.png': 'Neón Azul', 'marcoNeon2.png': 'Neón Verde',
                'marcoNeon3.png': 'Neón Rosa', 'marcoNeon4.png': 'Neón Naranja',
                'marcoNeon5.png': 'Neón Púrpura',
            }
            if frame_name in VALID_FRAMES:
                already_owned = request.user.frames.filter(frame_name=frame_name).exists()
                if not already_owned and request.user.wallet_balance >= 200:
                    request.user.wallet_balance -= 200
                    request.user.save()
                    UserFrame.objects.create(user=request.user, frame_name=frame_name)
                    Purchase.objects.create(house=house, buyer=request.user, item_name=f"🖼️ {FRAME_LABELS.get(frame_name, frame_name)}", currency_type='saldo', amount=200)
                
        elif action == "buy_bedroom_wallcolor":
            if request.user.wallet_balance >= 80 and not profile.unlock_wallcolor:
                request.user.wallet_balance -= 80
                request.user.save()
                profile.unlock_wallcolor = True
                profile.save()
                Purchase.objects.create(house=house, buyer=request.user, item_name="🎨 Color de Pared (Dormitorio)", currency_type='saldo', amount=80)

        elif action == "buy_bedroom_stars_rug":
            if request.user.wallet_balance >= 120 and not profile.unlock_stars_rug:
                request.user.wallet_balance -= 120
                request.user.save()
                profile.unlock_stars_rug = True
                profile.bedroom_rug_style = 'rug_stars'
                profile.save()
                Purchase.objects.create(house=house, buyer=request.user, item_name="⭐ Alfombra Estelar (Dormitorio)", currency_type='saldo', amount=120)

        elif action == "buy_bedroom_poster_gaming":
            if request.user.wallet_balance >= 150 and not profile.unlock_poster_gaming:
                request.user.wallet_balance -= 150
                request.user.save()
                profile.unlock_poster_gaming = True
                profile.bedroom_poster = 'poster_gaming'
                profile.save()
                Purchase.objects.create(house=house, buyer=request.user, item_name="🎮 Poster Gaming (Dormitorio)", currency_type='saldo', amount=150)

        return redirect('tienda', house_slug=house.slug)
        
    from accounts.models import UserFrame
    from .models import Purchase
    FRAMES = [
        {'name': 'marco1.png',     'label': 'Marco Dorado',    'emoji': '🔶'},
        {'name': 'marco3.png',     'label': 'Marco Elegante',  'emoji': '✨'},
        {'name': 'marcoNeon1.png', 'label': 'Neón Azul',       'emoji': '💙'},
        {'name': 'marcoNeon2.png', 'label': 'Neón Verde',      'emoji': '💚'},
        {'name': 'marcoNeon3.png', 'label': 'Neón Rosa',       'emoji': '🩷'},
        {'name': 'marcoNeon4.png', 'label': 'Neón Naranja',    'emoji': '🧡'},
        {'name': 'marcoNeon5.png', 'label': 'Neón Púrpura',    'emoji': '💜'},
    ]
    owned_frame_names = list(request.user.frames.values_list('frame_name', flat=True))
    custom_rewards = house.custom_rewards.all().order_by('-created_at')
    purchases = house.purchases.all().select_related('buyer')[:100]
    
    return render(request, "tienda.html", {
        "house": house, 
        "profile": profile,
        "frames": FRAMES,
        "owned_frame_names": owned_frame_names,
        "custom_rewards": custom_rewards,
        "purchases": purchases,
    })


from django.http import JsonResponse

@login_required
def api_shopping_checksum(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    items = house.shopping_items.all().order_by('id')
    checksum_str = "|".join([f"{item.id}:{item.is_checked}" for item in items])
    return JsonResponse({'checksum': checksum_str})

@login_required
def api_store_checksum(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    # El estado de la tienda global cambia cuando gifs_unlocked o spent_points varían
    checksum_str = f"{house.gifs_unlocked}:{house.spent_points}"
    return JsonResponse({'checksum': checksum_str})

@login_required
def crear_recompensa(request, house_slug):
    from .models import CustomReward
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
        
    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        price = request.POST.get('price', 50)
        currency_type = request.POST.get('currency_type', 'points')
        image = request.FILES.get('image')
        
        CustomReward.objects.create(
            house=house,
            creator=request.user,
            title=title,
            description=description,
            price=price,
            currency_type=currency_type,
            image=image
        )
    return redirect('tienda', house_slug=house.slug)

@login_required
def canjear_recompensa(request, house_slug, reward_id):
    from .models import CustomReward, Purchase
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
        
    reward = get_object_or_404(CustomReward, id=reward_id, house=house)
    
    if request.method == "POST":
        if reward.currency_type == 'points':
            if house.available_points >= reward.price:
                house.spent_points += reward.price
                house.save()
                Purchase.objects.create(house=house, buyer=request.user, item_name=f"🎁 {reward.title}", currency_type='puntos', amount=reward.price, is_custom_reward=True)
                messages.success(request, f'¡Recompensa "{reward.title}" canjeada con éxito!')
            else:
                messages.error(request, f'No hay puntos suficientes en el bote para canjear "{reward.title}".')
        elif reward.currency_type == 'saldo':
            if request.user.wallet_balance >= reward.price:
                request.user.wallet_balance -= reward.price
                request.user.save()
                Purchase.objects.create(house=house, buyer=request.user, item_name=f"🎁 {reward.title}", currency_type='saldo', amount=reward.price, is_custom_reward=True)
                messages.success(request, f'¡Recompensa "{reward.title}" canjeada con éxito!')
            else:
                messages.error(request, f'No tienes saldo suficiente para canjear "{reward.title}".')
                
    return redirect('tienda', house_slug=house.slug)

@login_required
def eliminar_recompensa(request, house_slug, reward_id):
    from .models import CustomReward
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
        
    reward = get_object_or_404(CustomReward, id=reward_id, house=house)
    if reward.creator == request.user or request.user == house.owner:
        if request.method == "POST":
            reward.delete()
            
    return redirect('tienda', house_slug=house.slug)
