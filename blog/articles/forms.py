from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Article, GalleryPost, UserProfile


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


class ArticleCreateForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ('title', 'excerpt', 'content', 'published_at')
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'published_at': forms.DateInput(attrs={'type': 'date'}),
        }


class GalleryPostForm(forms.ModelForm):
    class Meta:
        model = GalleryPost
        fields = ('title', 'category', 'image')
        widgets = {
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*', 'class': 'custom-file-input'}),
        }
