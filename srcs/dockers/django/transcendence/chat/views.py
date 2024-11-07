from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from members.decorator import personalised_login_required

# Create your views here.
@personalised_login_required
def chat(request):
    if request.method == "GET":
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'chat.html')
        return redirect('index2', goto='chat')
    else:
        return JsonResponse({'error': 'Invalid request'})