from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db import models
from django.core.exceptions import ValidationError
import re

# Rôle: Définir la structure des données de votre application.
# En d'autres termes, models.py contient les définitions des modèles de données,
# qui correspondent généralement aux tables de la base de données.


# Validateur personnalisé
def validate_alphanumeric(value):
    if not re.match("^[a-zA-Z0-9]*$", value):
        raise ValidationError(
            '%(value)s ne contient pas uniquement des caractères alphanumériques',
            params={'value': value},
        )


class MyUserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, tournamentName=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(username, email, password)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class myUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=False)
    username = models.CharField(
        max_length=16,
        unique=True,
        validators=[validate_alphanumeric]  # Ajout du validateur personnalisé
    )
    tournamentName = models.CharField(
        max_length=16,
        validators=[validate_alphanumeric]  # Ajout du validateur personnalisé
        
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    friends = models.ManyToManyField("self", symmetrical=True, blank=True)
    pending_friends = models.ManyToManyField("self", symmetrical=False, related_name='pending_friend_requests', blank=True)
    GuysWhoWantToBeMyFriend = models.ManyToManyField("self", symmetrical=False, related_name='guys_friend', blank=True)
    mutedUsers = models.ManyToManyField("self", symmetrical=False, related_name='muted_users', blank=True)
    waitingNotifications = models.ManyToManyField("self", symmetrical=False, related_name='waiting_notifications', blank=True)



    intra_id = models.IntegerField(null=True, default=0)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.gif')

    is_online = models.BooleanField(default=False)
    is_playing = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    groups = models.ManyToManyField(
        Group,
        related_name='myuser_set',  # Change related_name to avoid clashes
        blank=True,
        help_text='The groups this user belongs to.',
        related_query_name='myuser',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='myuser_set',  # Change related_name to avoid clashes
        blank=True,
        help_text='Specific permissions for this user.',
        related_query_name='myuser',
    )

    def __str__(self):
        return self.username