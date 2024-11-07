from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import random
import string
import requests
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from members.models import myUser
from .models import FriendRequest
from .forms import FriendRequestForm
from members.decorator import personalised_login_required
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


import logging

logger = logging.getLogger(__name__)

# Rôle: Gérer la logique métier et les interactions entre le modèle (données),
# les formulaires (saisie utilisateur), et les templates (affichage). views.py contient les
# fonctions ou classes qui récupèrent les données des modèles,
# les affichent à l'utilisateur via les templates, et gèrent les soumissions de formulaires.


# Create your views here.
@personalised_login_required
def friend(request):
    if request.method == "GET":
        pending_friends_count = request.user.GuysWhoWantToBeMyFriend.count()
        context = {
            'friends': request.user.friends.all(),
            'pending_friends': request.user.pending_friends.all(),
            'GuysWhoWantToBeMyFriend': request.user.GuysWhoWantToBeMyFriend.all(),
            'form': FriendRequestForm(),
            'is_online': request.user.is_online,
            'pending_friends_count': pending_friends_count,
        }
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'friend.html', context)
        return redirect('index2', goto='friend')
    else:
        return JsonResponse({'error': 'Invalid request'})

@personalised_login_required
@csrf_exempt
def add_friend(request):
    if request.method == 'POST':
        form = FriendRequestForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                user = myUser.objects.get(username=username)
            except myUser.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found' , 'friendRequest': True})
            if user == request.user:
                return JsonResponse({'success': False, 'error': 'You cannot add yourself as a friend' , 'friendRequest': True})
            if user in request.user.friends.all():
                return JsonResponse({'success': False, 'error' :'User is already your friend' , 'friendRequest': True})
            if FriendRequest.objects.filter(from_user=request.user, to_user=user).exists():
                return JsonResponse({'success': False, 'error': 'Friend request already sent' , 'friendRequest': True})
            request.user.pending_friends.add(user)
            user.GuysWhoWantToBeMyFriend.add(request.user)
            # Envoyer la notification
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}",
                {
                    "type": "friend_request_notification",
                    "user": request.user.username
                }
            )
            return JsonResponse({'success': True , 'friendRequest': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid form data' , 'friendRequest': True})
    return HttpResponseBadRequest('Invalid request method')


@personalised_login_required
@csrf_exempt
def accept_friend(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user = myUser.objects.get(username=username)
        except myUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found' , 'friendRequest': True})
        if user not in request.user.pending_friend_requests.all():
            return JsonResponse({'success': False, 'error': 'Friend request not found' , 'friendRequest': True})
        request.user.pending_friend_requests.remove(user)
        request.user.GuysWhoWantToBeMyFriend.remove(user)
        request.user.friends.add(user)
        user.friends.add(request.user)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",
            {
                "type": "friend_request_accepted",
                "user": request.user.username
            }
        )
        return JsonResponse({'success': True , 'friendRequest': True})
    return HttpResponseBadRequest('Invalid request method')


@personalised_login_required
@csrf_exempt
def remove_friend(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user = myUser.objects.get(username=username)
        except myUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found' , 'friendRequest': True})
        if user not in request.user.friends.all():
            return JsonResponse({'success': False, 'error': 'User not in your friends list' , 'friendRequest': True})
        request.user.friends.remove(user)
        user.friends.remove(request.user)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",
            {
                "type": "friend_request_removed",
                "user": request.user.username
            }
         )
        return JsonResponse({'success': True, 'friendRequest': True})
    return HttpResponseBadRequest('Invalid request method')

@personalised_login_required
def update_friend(request):
    if request.method == 'GET':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'friend_update.html')
    else:
        return render(request, 'index.html')