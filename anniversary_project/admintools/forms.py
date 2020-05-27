from django import forms
from django.forms import ModelForm, Form

from .models import AdminTool, AdminToolDeploymentSchema


class AdminToolForm(ModelForm):
    tool_description = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = AdminTool
        fields = ['tool_id', 'tool_title', 'tool_description']

    def save_with_script(self, script_str: str, permanent=False):
        self.instance.save_with_script(script_str)
        if permanent:
            self.instance.make_permanent()


class AdminToolDeployForm(ModelForm):
    class Meta:
        model = AdminToolDeploymentSchema
        fields = ['admintool', 'sleep_seconds']


class SystemLogQueryForm(Form):
    max_lines = forms.ChoiceField(
        choices=(
            ('100', '100'),
            ('200', '200'),
            ('500', '500'),
        )
    )
