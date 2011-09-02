from django.forms import ModelForm
from fbook.models import *
from django import forms

class SuggestionForm(ModelForm):
    suggestion = forms.CharField(widget=forms.Textarea(attrs={'rows':'10','cols':'70'}))
    class Meta:
        model = Suggestion
        fields = ('title','suggestion',)

class MessageForm(ModelForm):
    class Meta:
        model = Like
        fields = ('msg',)

class LikeForm(ModelForm):
    class Meta:
        model = Like
        fields = ('msg',)

class FbookUserForm(ModelForm):
    class meta:
        model = FbookUser
        fields = ('uid',)
