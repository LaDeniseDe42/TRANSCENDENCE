from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


# Create your models here.

class FriendRequest(models.Model):
    from_user = models.ForeignKey('members.myUser', related_name='from_user', on_delete=models.CASCADE)
    to_user = models.ForeignKey('members.myUser', related_name='to_user', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Friend request from {self.from_user} to {self.to_user}'

    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['date']


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=(('online', 'En ligne'), ('offline', 'Hors ligne')), default='offline')

    def get_status_display(self):
        # Retourne la représentation textuelle du statut
        return dict((('online', 'En ligne'), ('offline', 'Hors ligne'))).get(self.status, 'Inconnu')

    def get_status_class(self):
        # Retourne une classe CSS basée sur le statut
        if self.status == 'online':
            return 'status-online'
        elif self.status == 'offline':
            return 'status-offline'
        else:
            return 'status-unknown'