from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from houses.models import House

@login_required
def chat_index(request, house_slug):
    house = get_object_or_404(House, slug=house_slug)
    if request.user not in house.members.all():
        return redirect('inicio')
    return render(request, "chats.html", {"house": house})
