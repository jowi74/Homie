from django.contrib import messages
from accounts.models import Achievement, UserAchievement
from housebedrooms.models import HouseProfile

def check_achievements(request, user):
    """
    Evalúa todos los logros que el usuario aún NO tiene.
    Si cumple las condiciones, se le otorga, se le suma el saldo y lanza un flash message.
    """
    if not user.is_authenticated:
        return

    # 1. Obtener stats globales del usuario sumando sus perfiles de casa
    profiles = HouseProfile.objects.filter(user=user)
    
    total_tasks = sum(p.completed_tasks_count for p in profiles)
    total_shopping = sum(p.completed_shopping_count for p in profiles)
    total_points = sum(p.points for p in profiles)
    total_houses = user.houses.count()
    total_messages = user.sent_messages.count()
    
    stats = {
        'tasks': total_tasks,
        'shopping': total_shopping,
        'points': total_points,
        'houses': total_houses,
        'messages': total_messages
    }
    
    unlocked_ids = user.achievements.values_list('achievement_id', flat=True)
    pending_achievements = Achievement.objects.exclude(id__in=unlocked_ids)
    
    for ach in pending_achievements:
        current_val = stats.get(ach.condition_type, 0)
        
        if current_val >= ach.target_value:
            # ¡Logro conseguido!
            UserAchievement.objects.create(user=user, achievement=ach)
            user.wallet_balance += ach.reward_saldo
            user.save(update_fields=['wallet_balance'])
            
            if request:
                messages.success(request, f"🏆 ¡Logro Desbloqueado: {ach.name}! 🎉 (+{ach.reward_saldo} Saldo personal)")
