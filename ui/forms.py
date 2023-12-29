from django import forms
from django.core.validators import RegexValidator


class FediverseLoginForm(forms.Form):
    instance = forms.CharField(
        label='Instance',
        max_length=100,
        validators=[RegexValidator(r'^[A-Za-z0-9.]+[A-Za-z0-9.-]*[A-Za-z0-9]+$', 'incorrect format')],
        widget=forms.TextInput(attrs={'placeholder': 'misskey.io'})
    )


class NewPostForm(forms.Form):
    content = forms.CharField(label='Content', widget=forms.Textarea)
    attachment = forms.FileField(label='Upload files', widget=forms.ClearableFileInput(), required=False)