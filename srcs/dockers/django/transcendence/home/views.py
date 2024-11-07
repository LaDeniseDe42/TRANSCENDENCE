from django.shortcuts import render, redirect
from django.http import JsonResponse

# Create your views here.
def index(request):
    return render(request, 'index.html')

def index2(request, goto):
    goto = goto.replace('_', '/')
    return render(request, 'index.html', {'goto': goto})

def navbar(request):
    if request.method == 'GET':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.headers.get('isUpdateBySPA') == 'navbarUpdateSPA':
            return render(request, 'navbar.html')
        else:
            return redirect('home')
    else:
        return JsonResponse({'error': 'Invalid request'})

def home(request):
    if request.method == 'GET':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'home.html')
        else:
            return redirect('index')
    else:
        return JsonResponse({'error': 'Invalid request'})
