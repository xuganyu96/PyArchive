from django import forms
from django.forms import ModelForm

from .models import AdminTool


class AdminToolForm(ModelForm):
    tool_description = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = AdminTool
        fields = ['tool_id', 'tool_title', 'tool_description']

    def save_with_script(self, script_str: str, permanent=False):
        self.instance.save_with_script(script_str)
        if permanent:
            self.instance.make_permanent()
