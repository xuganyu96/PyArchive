import django
from django.conf import settings

#   You need to set up project settings before being able to access models within Django Apps outside Django
from anniversary_project.settings import DATABASES, INSTALLED_APPS
settings.configure(DATABASES=DATABASES, INSTALLED_APPS=INSTALLED_APPS)
django.setup()
print('--Django settings initialized--')