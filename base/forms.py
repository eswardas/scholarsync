from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Room, Message, UserProfile

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = user.username.lower()
        if commit:
            user.save()
            # Create profile automatically
            UserProfile.objects.get_or_create(user=user)
        return user
class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'topic', 'description', 'study_type', 'max_participants']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'topic': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'study_type': forms.Select(attrs={'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your message here...'
            })
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'avatar', 'preferred_study_time']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'preferred_study_time': forms.Select(attrs={'class': 'form-control'}),
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }