from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from houses.models import House
from .models import Task
from accounts.models import CustomUser
from housebedrooms.models import HouseProfile
from django.http import JsonResponse
from accounts.utils import check_achievements


@login_required
def lista_tareas(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
        
    pending_tasks = house.tasks.filter(is_completed=False, has_been_completed=False).order_by('created_at')
    incomplete_tasks = house.tasks.filter(is_completed=False, has_been_completed=True).order_by('-created_at')
    completed_tasks = house.tasks.filter(is_completed=True).order_by('-created_at')
    tasks = house.tasks.all() # Para el condicional global
    
    if request.method == "POST":
        
        title = request.POST.get('title')
        points = request.POST.get('points', 10)
        assigned_to_id = request.POST.get('assigned_to')
        
        if title:
            assigned_user = None
            if assigned_to_id:
                try:
                    assigned_user = CustomUser.objects.get(username=assigned_to_id)
                except CustomUser.DoesNotExist:
                    pass
            Task.objects.create(house=house, title=title, points=points, assigned_to=assigned_user)
            return redirect('lista_tareas', house_slug=house.slug)
            
    return render(request, "tareas.html", {
        "house": house, 
        "tasks": tasks,
        "pending_tasks": pending_tasks,
        "incomplete_tasks": incomplete_tasks,
        "completed_tasks": completed_tasks
    })

@login_required
def marcar_tarea_completada(request, house_slug, task_id):
    house = get_object_or_404(House, slug=house_slug)
    if request.user in house.members.all():
        task = get_object_or_404(Task, id=task_id, house=house)
        if not task.is_completed:
            task.is_completed = True
            
            # Solo dar puntos la primera vez que se completa
            if not task.has_been_completed:
                task.has_been_completed = True
                profile, _ = HouseProfile.objects.get_or_create(user=request.user, house=house)
                profile.points += task.points
                profile.completed_tasks_count += 1
                profile.save()
                
            task.save()
            check_achievements(request, request.user)
    return redirect('lista_tareas', house_slug=house.slug)

@login_required
def deshacer_tarea(request, house_slug, task_id):
    house = get_object_or_404(House, slug=house_slug)
    if request.user in house.members.all():
        task = get_object_or_404(Task, id=task_id, house=house)
        if task.is_completed:
            task.is_completed = False
            task.save()
    return redirect('lista_tareas', house_slug=house.slug)

@login_required
def eliminar_tarea(request, house_slug, task_id):
    house = get_object_or_404(House, slug=house_slug)
    if request.user in house.members.all():
        task = get_object_or_404(Task, id=task_id, house=house)
        task.delete()
    return redirect('lista_tareas', house_slug=house.slug)

@login_required
def api_tasks_checksum(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    tasks = house.tasks.all().order_by('id')
    checksum_str = "|".join([f"{t.id}:{t.is_completed}:{t.has_been_completed}" for t in tasks])
    return JsonResponse({'checksum': checksum_str})
