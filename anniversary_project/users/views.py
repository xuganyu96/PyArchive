from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.forms import UserCreationForm


def register(request: HttpRequest) -> HttpResponse:
    user_creation_form = UserCreationForm()
    return render(request, 'users/register.html', {'user_creation_form': user_creation_form})
