from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from members.models import myUser
from django import forms


# Rôle: Définir les formulaires que les utilisateurs utiliseront pour interagir
# avec les modèles de données.
# forms.py transforme les données saisies par les utilisateurs en objets de modèles validés.


class FriendRequestForm(forms.Form):
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        help_text='Enter the username of the friend you want to add'
    )