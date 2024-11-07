from django.shortcuts import redirect

def personalised_login_required(function):
    def _function(request,*args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return function(request, *args, **kwargs)
    return _function

def personalised_Not_in_game_required(function):
    def _function(request,*args, **kwargs):
        if request.user.is_playing:
            return redirect('game')
        return function(request, *args, **kwargs)
    return _function