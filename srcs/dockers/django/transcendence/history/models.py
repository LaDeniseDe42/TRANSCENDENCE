from django.db import models
from members.models import myUser

# Create your models here.
class History(models.Model):
    game = models.CharField(max_length=30, choices=[('pong','Pong'), ('game2','Game2'), ('game3','Game3')])
    mode = models.CharField(max_length=30, choices=[('bot', 'Bot'), ('local', 'Local'), ('remote', 'Remote'),('tournament', 'Tournament')])
    winner = models.ForeignKey(myUser, related_name='won_games', on_delete=models.SET_NULL, null=True, blank=True)
    scoreW = models.IntegerField(default=0)
    scoreL = models.IntegerField(default=0)
    looser = models.ForeignKey(myUser, related_name='lost_games', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=30, null=True, blank=True)
    class Meta:
            verbose_name_plural = 'GameHistories'
        
def __str__(self):
    if self.name:  # Partie contre un bot
        return f"{self.winner.username if self.winner else 'Unknown'} won against bot {self.name} in ({self.mode})"
    elif self.name:  # Partie locale
        return f"{self.winner.username if self.winner else 'Unknown'} won against local player {self.name} in ({self.mode})"
    else:  # Partie entre utilisateurs
        return f"{self.winner.username if self.winner else 'Unknown'} won against {self.looser.username if self.looser else 'Unknown'} in ({self.mode})"

