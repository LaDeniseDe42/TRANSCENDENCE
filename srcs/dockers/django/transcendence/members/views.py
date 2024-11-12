from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from .forms import RegisterUserForm
from django.conf import settings
import random
import string
from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from .models import myUser
import requests
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from channels.layers import get_channel_layer
from django.contrib import messages
from asgiref.sync import async_to_sync
from members import consumers
from history.models import History
import re


import logging

logger = logging.getLogger(__name__)

from .decorator import personalised_login_required


def check_login_status(request):
    if not request.user.is_authenticated:
        return JsonResponse({'is_logged_in': False})
    else:
        return JsonResponse({'is_logged_in': True})

def reformat_uri(uri):
    uri = uri.replace(":", "%3A")
    return uri.replace("/", "%2F")


def homeMembers(request):
    if request.method == 'GET':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'members_home.html')
        else:
            return redirect('index2', goto='members')
    else:
        return JsonResponse({'error': 'Invalid request'})

@personalised_login_required
def profile(request):
    if request.method == 'GET':
        histo = History.objects.filter(winner__username=request.user.username) | History.objects.filter(looser__username=request.user.username)
        total = histo.count()
        nb_won = histo.filter(winner__username=request.user.username).count()
        nb_lost = histo.filter(looser__username=request.user.username).count()
        if total > 0 and nb_won > 0:
            ratio = nb_won / total
        else:
            ratio = 0
        data = {
            'username': request.user.username,
            'email': request.user.email,
            'avatar': request.user.avatar.url,
            'show_password_change': True,
            'nb_won': nb_won,
            'nb_lost': nb_lost,
            'ratio': ratio,
            'total': total,
        }
        if request.user.intra_id > 0:
            data['show_password_change'] = False
        if request.headers.get('partialUpdate') == True:
            return render(request, 'partial_profile.html', data)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'profile.html', data)
        else:
            return redirect('index2', goto='members_profile')
    else:
        return JsonResponse({'error': 'Invalid request'})
    
@personalised_login_required
def profile_discover(request, user_id):
    if request.method == 'GET':
        try:
            user = myUser.objects.get(id=user_id)
            histoWin = History.objects.filter(winner__username=user.username)
            histoLose = History.objects.filter(looser__username=user.username)
            total = histoWin.count() + histoLose.count()
            nb_won = histoWin.filter(winner__username=user.username).count()
            nb_lost = histoLose.filter(looser__username=user.username).count()
            if total > 0 and nb_won > 0:
                ratio = nb_won / total
            else:
                ratio = 0
            data = {
                'username': user.username,
                'email': user.email,
                'avatar': user.avatar.url,
                'user_id': user.id,
                'nb_won': nb_won,
                'nb_lost': nb_lost,
                'ratio': ratio,
                'total': total,
            }
        except myUser.DoesNotExist:
            data = {
                "username": "get rickrolled",
                "email": "you entered a wrong id",
                "avatar": "/media/avatars/rickroll.gif",
                'user_id': "you really think rickroll is a user id ?",
                'nb_won': 424242,
                'nb_lost': 0,
                'ratio': 1,
                'total': 424242,
            }
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'profile_discover.html', data)
        else:
            return redirect('index2', goto=f'members_profile_{user_id}')
    else:
        return JsonResponse({'error': 'Invalid request'})

@personalised_login_required
def profile_discover_reverse(request, user_name):
    if request.method == 'GET':
        data = {}
        try:
            user = myUser.objects.get(username=user_name)
            histoWin = History.objects.filter(winner__username=user.username)
            histoLose = History.objects.filter(looser__username=user.username)
            total = histoWin.count() + histoLose.count()
            nb_won = histoWin.filter(winner__username=user.username).count()
            nb_lost = histoLose.filter(looser__username=user.username).count()
            if total > 0 and nb_won > 0:
                ratio = nb_won / total
            else:
                ratio = 0
            data = {
                'username': user.username,
                'email': user.email,
                'avatar': user.avatar.url,
                'user_id': user.id,
                'nb_won': nb_won,
                'nb_lost': nb_lost,
                'ratio': ratio,
                'total': total,
            }
        except myUser.DoesNotExist:
            data = {
                "username": "get rickrolled",
                "email": "you entered a wrong username",
                "avatar": "/media/avatars/rickroll.gif",
                'user_id': "you really think rickroll is a user name ?",
                'nb_won': 424242,
                'nb_lost': 0,
                'ratio': 1,
                'total': 424242,
            }
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'profile_discover.html', data)
        else:
            return redirect('index2', goto=f'members_profile_{user_name}')
    else:
        return JsonResponse({'error': 'Invalid request'})

def loginPage(request):
    if request.method == 'GET':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if request.user.is_authenticated:
                return redirect('home')
            if settings.INTRA_42_CLIENT_ID == "":
                return render(request, 'login.html')
            intra_creds = {
                'redirect_uri': reformat_uri(settings.INTRA_42_REDIRECT_URI),
                'client_id': settings.INTRA_42_CLIENT_ID
            }
            return render(request, 'login.html', intra_creds)
        else:
            return redirect('index2', goto='members_login')
    elif request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.intra_id > 0:
                    return JsonResponse({'success': False, 'error': 'Intra user can\'t login with password'})
            else:
                try:
                    testIntra = myUser.objects.get(username=username)
                    if testIntra is not None:
                        if testIntra.intra_id > 0:
                            return JsonResponse({'success': False, 'error': 'Intra user can\'t login with password'})
                except myUser.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Invalid username'})
            if user is not None:
                login(request, user)
                return JsonResponse({'success': True, 'goto': 'home'})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid credentials'})
        else:
            return render(request, 'index.html')
    else:
        return JsonResponse({'error': 'Invalid request'})

def registerPage(request):
    if request.method == 'GET':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if request.user.is_authenticated:
                return redirect('home')
            return render(request, 'register.html')
        else:
            return redirect('index2', goto='members_register')
    elif request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            form = RegisterUserForm(request.POST)
            if form.is_valid():
                form.save()
                return JsonResponse({'success': True, 'goto': 'members/login'})
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
        else:
            return render(request, 'index.html')
    else:
        return JsonResponse({'error': 'Invalid request'})

def logoutSystem(request):
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            user = request.user
            request.user.is_online = False
            request.user.is_playing = False
            actualSessionID = request.COOKIES.get('sessionid')
            for consumer in list(consumers.sessionIDTable.keys()):
                if consumer in consumers.sessionIDTable:
                    if consumers.sessionIDTable[consumer] == actualSessionID:
                        try:
                            async_to_sync(consumer.disconnect)(666)
                        except Exception as e:
                            pass
            logout(request)
            user.is_online = False
            user.save()
            return JsonResponse({'success': True, 'goto': 'home'})
        else:
            return render(request, 'index.html')
    else:
        return JsonResponse({'error': 'Invalid request'})

@personalised_login_required
def updateProfile(request):
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            user = request.user
            changed_username = False
            actualPassword = request.POST.get("currentPassword","")
            newPassword1 = request.POST.get("newPassword1", "")
            newPassword2 = request.POST.get("newPassword2", "")
            email = request.POST.get("newEmail", "")
            username = request.POST.get("newUsername", "")
            profilePic = request.FILES.get('profilePicture')
            # changing password
            errors_get = {}
            if newPassword1:
                if newPassword1 == newPassword2:
                    if user.check_password(actualPassword):
                        user.set_password(newPassword1)
                    else:
                        errors_get['currentPassword'] = 'Invalid password'
                else:
                    errors_get['newPassword2'] = 'Passwords do not match'
            # changing email
            if email:
                validator = EmailValidator()
                try:
                    validator(email)
                    user.email = email
                except ValidationError:
                    errors_get['email'] = 'Invalid email'
            # changing username
            if username:
                if myUser.objects.filter(username=username).exists():
                    errors_get['username'] = 'Username already taken'
                elif len(username) > 16:
                    errors_get['username'] = 'Username too long'
                elif not re.match("^[a-zA-Z0-9]*$", username):
                    errors_get['username'] = 'Username must be alphanumeric'
                else:
                    user.username = username
                    changed_username = True
            # changing profile picture
            if profilePic:
                if not profilePic.content_type.startswith('image'):
                    errors_get['profilePicture'] = 'Invalid file type'
                else:
                    user.avatar = profilePic
            if errors_get:
                return JsonResponse({'success': False, 'errors': errors_get})
            else:
                user.save()
                if changed_username == True:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        "all_users",
                        {
                            "type": "username_change_notification",
                            "user": user.username
                        }
                    )
                return JsonResponse({'success': True, 'goto': 'members/profile', 'profileUpdate': True})
            
            
    else:
        return JsonResponse({'error': 'Invalid request'})



def generate_state():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))



def login_intra(request):
    state = generate_state()
    request.session['oauth_state'] = state  # Save state in session for later verification

    auth_url = (
        "https://api.intra.42.fr/oauth/authorize"
        "?client_id={client_id}"
        "&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=public"
        "&state={state}"
    ).format(
        client_id=settings.INTRA_42_CLIENT_ID,
        redirect_uri=settings.INTRA_42_REDIRECT_URI,
        state=state
    )
    return redirect(auth_url)




def profile_intra(request):

    code = request.GET.get('code')
    state = request.GET.get('state')
    if not code or not state:
        if 'error' in request.GET:
            messages.error(request, f"An error occurred during authentication: {request.GET['error']}")
        else:
            messages.error(request, "An error occurred during authentication. Please try again.")
        return redirect('login')

    try:
        # Échanger le code d'autorisation contre un jeton d'accès
        token_url = "https://api.intra.42.fr/oauth/token"
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': settings.INTRA_42_CLIENT_ID,
            'client_secret': settings.INTRA_42_CLIENT_SECRET,
            'code': code,
            'redirect_uri': settings.INTRA_42_REDIRECT_URI,
            'state': state,
        }
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()  # Lever une exception pour les erreurs HTTP
        token_json = token_response.json()
        access_token = token_json.get('access_token')

        # Utiliser le jeton d'accès pour obtenir les informations de l'utilisateur
        user_info_url = "https://api.intra.42.fr/v2/me"
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info_response.raise_for_status()  # Lever une exception pour les erreurs HTTP

        user_info = user_info_response.json()

        # Vérifier si le username existe déjà dans la base de données
        username = user_info['login']
        if myUser.objects.filter(username=username).exists():
            # Générer un nouveau username unique
            username = f"{username}_{generate_state()[:6]}"  # Ajoute un suffixe aléatoire au username

        # Créer ou mettre à jour l'utilisateur dans votre base de données Django
        new_mdp = myUser.objects.make_random_password(length=12, allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789')
        user, created = myUser.objects.get_or_create(
            intra_id=user_info['id'],
            defaults={
                'email': user_info['email'],
                'username': username,
                'password': make_password(new_mdp),
            }
        )
        if created:
            download_image(user, user_info['image']['versions']['large'])

        # Authentifier l'utilisateur dans Django
        login(request, user)
        return redirect('index')

    except requests.RequestException as e:
        return JsonResponse({'success': False, 'error': f"HTTP request failed: {e}"})

    except Exception as e:
        return JsonResponse({'success': False, 'error': f"An error occurred: {e}"})
    

def download_image(instance, url):
    response = requests.get(url)
    if response.status_code != 200:
        return
    instance.avatar.save(f'{instance.username}.jpg', ContentFile(response.content), save=True)
    instance.save()
    # return instance.avatar.url