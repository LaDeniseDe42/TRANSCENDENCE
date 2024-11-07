from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from members.decorator import personalised_login_required, personalised_Not_in_game_required
from django.views.decorators.http import require_GET
import uuid
from members.models import myUser, validate_alphanumeric



@personalised_login_required
def game(request):
    if request.method == 'GET':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'game.html')
        else:
            return redirect('index2', goto='game')
    else:
        return JsonResponse({'error': 'Invalid request'})

@personalised_login_required
@personalised_Not_in_game_required
def single(request):
    if request.method == 'GET':
        data = {
            'username': request.user.username,
            'avatar': request.user.avatar.url,
        }
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'single.html', data)
        else:
            return redirect('index2', goto='game_single')
    else:
        return JsonResponse({'error': 'Invalid request'})

@personalised_login_required
@personalised_Not_in_game_required
def multi(request):
    if request.method == 'GET':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'multi.html')
        else:
            return redirect('index2', goto='game_multi')
    else:
        return JsonResponse({'error': 'Invalid request'})
@personalised_login_required
@personalised_Not_in_game_required
def multi4(request):
    if request.method == 'GET':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'multi4.html')
        else:
            return redirect('index2', goto='game_multi4')
    else:
        return JsonResponse({'error': 'Invalid request'})

from .consumers import tournamentConsumers

@personalised_login_required
@personalised_Not_in_game_required
def tournament(request):
    if request.method == 'GET':
        data = {
            'username': request.user.username,
            'avatar': request.user.avatar.url,
        }
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'tournament.html', data)
        else:
            return redirect('index2', goto='game_tournament')
    elif request.method == 'POST':
        # guyIsInTournament = False
        # for tournamentId, tournament in tournamentConsumers.tournaments.items():
        #     if tournament.get('tournamentEnded', False) == True:
        #         continue
        #     if request.user in tournament['players']:
        #         guyIsInTournament = True
        #         break
        # if guyIsInTournament == False:
        if tournamentConsumers.tournamentLaunched >= 1:
            return JsonResponse({'success': False, 'error': 'Sorry server is busy, try again later'})
        nick = request.headers.get("tournamentNick", "")
        if nick == "":
            return JsonResponse({'success': False, 'error': 'Invalid nickname'})
        try:
            validate_alphanumeric(nick)
            if len(nick) > 16:
                return JsonResponse({'success': False, 'error': 'Nickname too long'})
            request.user.tournamentName = nick + '_' + str(request.user.id)
            request.user.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request'})


@personalised_login_required
def remote(request):
    if request.method == 'GET':
        room_id = request.GET.get('room')
        if room_id is None:
            request.user.is_Playing = False
            request.user.save()
            return redirect('home')

        p1 = room_id.split('VS')[0]
        #retirer REMOTE_ pour garder la suite
        p1 = p1[7:]
        #rechercher l'username de p1 et p2 enfonction de l'id de chaque user
        p1 = myUser.objects.get(id=p1).username
        p2 = room_id.split('VS')[1]
        p2 = p2[:-1]
        p2 = myUser.objects.get(id=p2).username
        data = {
            'username': request.user.username,
            'avatar': request.user.avatar,
            'room': room_id,
            'p1': p1,
            'p2': p2,
        }
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'remote.html', data)
        else:
            return redirect('index2', goto='game_remote')
    else:
        return JsonResponse({'error': 'Invalid request'})
    
@personalised_login_required
@personalised_Not_in_game_required
def waiting(request):
    if request.method == 'GET':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'waitingPlayer.html')
        else:
            return redirect('index2', goto='game_waiting')
    else:
        return JsonResponse({'error': 'Invalid request'})
    
# Simuler l'état du matchmaking
matchmaking_status = {
    'match_found': False
}


# Exemple de mise à jour de l'état du matchmaking (à appeler lorsque deux joueurs sont trouvés)
def update_matchmaking_status():
    global matchmaking_status
    matchmaking_status['match_found'] = True
    return JsonResponse({'status': 'success'})

def tournamentGames(request):
    if request.method == 'GET':
        room_id = request.GET.get('room')
        if room_id is None:
            request.user.is_Playing = False
            request.user.save()
            return redirect('home')
        data = {
            'username': request.user.username,
            'tournamentName': request.user.tournamentName,
        }
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'tournamentGame.html', data)
        else:
            return redirect(f'index2', goto='game_tournament_game_{room_id}')
    else:
        return JsonResponse({'error': 'Invalid request'})