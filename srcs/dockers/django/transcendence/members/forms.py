from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.models import User
from .models import myUser
from django import forms


# Rôle: Définir les formulaires que les utilisateurs utiliseront pour interagir
# avec les modèles de données.
# forms.py transforme les données saisies par les utilisateurs en objets de modèles validés.

User = get_user_model()

class RegisterUserForm(UserCreationForm):
	email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control'}), required=True, error_messages={'required': 'Email is required'})
	username = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}), required=True, error_messages={'required': 'Username is required'})
	password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}), required=True, error_messages={'required': 'Password is required'})
	password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}), required=True, error_messages={'required': 'Password confirmation is required'})

	class Meta:
		model = myUser
		fields = ('username', 'email', 'password1', 'password2')


	def __init__(self, *args, **kwargs):
		super(RegisterUserForm, self).__init__(*args, **kwargs)

		self.fields['username'].widget.attrs['class'] = 'form-control'
		self.fields['password1'].widget.attrs['class'] = 'form-control'
		self.fields['password1'].label = 'Password'
		self.fields['password2'].widget.attrs['class'] = 'form-control'
		self.fields['password2'].label = 'Password Confirmation'
	
	def clean_username(self):
		username = self.cleaned_data.get('username')
		if User.objects.filter(username=username).exists():
			raise forms.ValidationError('This username is already taken. Please choose another one.')
		return username

	def clean_email(self):
		email = self.cleaned_data.get('email')
		return email