from django.forms import ModelForm

from .models import Archive


class ArchiveForm(ModelForm):
    class Meta:
        model = Archive
        fields = ['archive_file', 'archive_name']
