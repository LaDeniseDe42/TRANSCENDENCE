from django.urls import re_path
from . import consumers


websocketGame_urlpatterns = [
    re_path(r'ws/matchmaking/$', consumers.MatchmakingConsumer.as_asgi()),
    re_path(r'ws/pong/(?P<room_id>\w+)/$', consumers.gameConsumers.as_asgi()),
    re_path(r'ws/localStatus/$', consumers.localStatusIsPlayingConsumer.as_asgi()),
    re_path(r'ws/tournament/$', consumers.tournamentConsumers.as_asgi()),
    re_path(r'ws/tournament_game/(?P<room_id>\w+)/$', consumers.gameConsumers.as_asgi()),
]
