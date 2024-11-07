from .models import History
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.http import JsonResponse
from members.decorator import personalised_login_required
# Create your views here.

@personalised_login_required
def history_list(request):
    if request.method == 'GET':
        histo = History.objects.filter(winner__username=request.user.username) | History.objects.filter(looser__username=request.user.username)
        total = histo.count()
        nb_won = histo.filter(winner__username=request.user.username).count()
        nb_lost = histo.filter(looser__username=request.user.username).count()
        total_points_scored = 0
        total_points_taken = 0
        for game in History.objects.filter(winner__username=request.user.username):
            total_points_scored += game.scoreW
            total_points_taken += game.scoreL
        for game in History.objects.filter(looser__username=request.user.username):
            total_points_scored += game.scoreL
            total_points_taken += game.scoreW           
        if total > 0 and nb_won > 0:
            ratio = nb_won / total
        else:
            ratio = 0
        stats = {
            'nb_won': nb_won,
            'nb_lost': nb_lost,
            'ratio': ratio,
            'total': total,
        }
        point = {
            'scored': total_points_scored,
            'taken': total_points_taken  
        }    
        data = {
            'generalstats' : stats,
            'point' : point,
            'username': request.user.username,
            'history': histo
        }
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'history_list.html', data)
        else:
            return redirect('index2', goto='history')
    else:
        return JsonResponse({'error': 'Invalid request'})