from django.urls import re_path

from . import consumers

websocketStatus_urlpatterns = [
    re_path(r"ws/status/$", consumers.statusConsumer.as_asgi()),
]