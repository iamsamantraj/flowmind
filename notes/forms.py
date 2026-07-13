from django import forms
from .models import Note, Tag


class NoteForm(forms.ModelForm):
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Add tags separated by commas (e.g. work, ideas)'
        })
    )

    class Meta:
        model = Note
        fields = ['title', 'content', 'is_pinned']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Note title...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your note here...',
                'rows': 10
            }),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }