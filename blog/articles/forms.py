import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User

from .models import Article, GalleryPost, UserProfile




class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = ''

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


class PasswordResetCodeRequestForm(forms.Form):
    email = forms.EmailField()


class PasswordResetCodeConfirmForm(forms.Form):
    email = forms.EmailField()
    code = forms.CharField(max_length=6, min_length=6)
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_code(self):
        code = (self.cleaned_data.get('code') or '').strip()
        if not code.isdigit():
            raise forms.ValidationError('Code must contain 6 digits.')
        return code

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', 'The two password fields did not match.')

        if password1:
            try:
                validate_password(password1)
            except forms.ValidationError as exc:
                self.add_error('new_password1', exc)

        return cleaned_data


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
            'phone_number': forms.TextInput(attrs={'inputmode': 'numeric', 'pattern': '[0-9]*'}),
        }

    def clean_phone_number(self):
        phone_number = (self.cleaned_data.get('phone_number') or '').strip()
        if phone_number and not re.fullmatch(r'\d+', phone_number):
            raise forms.ValidationError('Phone number must contain numbers only.')
        return phone_number


class UserAccountForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class ArticleCreateForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = (
            'title',
            'author_name',
            'featured_image',
            'content',
            'publish_status',
            'scheduled_publish_at',
            'published_at',
            'allow_comments',
            'visibility',
        )
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'author_bio': forms.Textarea(attrs={'rows': 3}),
            'published_at': forms.DateInput(attrs={'type': 'date'}),
            'scheduled_publish_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'featured_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'maxlength': 200})


class GalleryPostForm(forms.ModelForm):
    class Meta:
        model = GalleryPost
        fields = ('title', 'category', 'image')
        widgets = {
            'category': forms.Select(attrs={'class': 'gallery-category-select'}),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*', 'class': 'custom-file-input'}),
        }
