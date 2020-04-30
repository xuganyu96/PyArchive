from django.forms import ModelForm

from .models import S3Connection


class S3ConnectionCreateForm(ModelForm):
    class Meta:
        model = S3Connection
        fields = ['connection_name',
                  'access_key',
                  'secret_key',
                  'region_name']
