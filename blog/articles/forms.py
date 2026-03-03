from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Article, ContactMessage, UserProfile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Email is already registered.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if len(username) < 4:
            raise forms.ValidationError('Username must be at least 4 characters long.')
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class AdminLoginForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': 'Please enter a correct admin username and password.',
    }

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not (user.is_staff or user.is_superuser):
            raise forms.ValidationError(
                'This account is not allowed to access the admin dashboard.',
                code='invalid_login',
            )


class ContactForm(forms.Form):
    name = forms.CharField(min_length=2, max_length=100)
    email = forms.EmailField()
    subject = forms.CharField(min_length=5, max_length=150)
    message = forms.CharField(min_length=20, widget=forms.Textarea)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('profile_image', 'age', 'phone_number', 'location', 'fashion_style', 'about_self')
        widgets = {
            'about_self': forms.Textarea(attrs={'rows': 5}),
            'profile_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }


class UserAccountForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class AdminArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ('title', 'slug', 'excerpt', 'content', 'author', 'is_trending', 'published_at')
        widgets = {
            'excerpt': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 8}),
            'published_at': forms.DateInput(attrs={'type': 'date'}),
        }


class AdminContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'subject', 'message')
        widgets = {
            'message': forms.Textarea(attrs={'rows': 6}),
        }


class AdminUserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('age', 'fashion_style', 'phone_number', 'location', 'about_self', 'profile_image')
        widgets = {
            'about_self': forms.Textarea(attrs={'rows': 5}),
            'profile_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }
