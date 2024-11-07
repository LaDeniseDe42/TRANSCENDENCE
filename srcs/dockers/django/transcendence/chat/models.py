from django.db import models
from members.models import myUser

class Message(models.Model):
    user = models.ForeignKey(myUser, on_delete=models.CASCADE)
    room_name = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} in {self.room_name}: {self.content[:50]}"