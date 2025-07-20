from django import forms
from .models import CodeSubmission
from core.models import Problem

LANGUAGE_CHOICES = [
    ("py", "Python"),
    ("c", "C"),
    ("cpp", "C++"),
]

class CodeSubmissionForm(forms.ModelForm):
    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'border-radius: 8px; border: 1px solid #d1d9e6; padding: 0.75rem 1rem; background: #f7fafd;'
        })
    )
    code = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 15,
            'placeholder': 'Enter your code here...',
            'style': 'border-radius: 8px; border: 1px solid #d1d9e6; padding: 0.75rem 1rem; background: #f7fafd; font-family: monospace;'
        })
    )
    input_data = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Enter input data (optional)...',
            'style': 'border-radius: 8px; border: 1px solid #d1d9e6; padding: 0.75rem 1rem; background: #f7fafd; font-family: monospace;'
        })
    )
    problem = forms.ModelChoiceField(
        queryset=Problem.objects.all(),
        required=False,
        empty_label="Select a problem (optional)",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'border-radius: 8px; border: 1px solid #d1d9e6; padding: 0.75rem 1rem; background: #f7fafd;'
        })
    )

    class Meta:
        model = CodeSubmission
        fields = ["problem", "language", "code", "input_data"]