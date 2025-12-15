from django import forms
from django.forms.models import inlineformset_factory
from tinymce.widgets import TinyMCE
from .models import Course, Module

class CourseForm(forms.ModelForm):
    overview = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 20}))
    
    class Meta:
        model = Course
        fields = ['subject', 'title', 'slug', 'overview']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
        }

ModuleFormSet = inlineformset_factory(
    Course,
    Module,
    fields=['title', 'description'],
    extra=2,
    can_delete=True
)