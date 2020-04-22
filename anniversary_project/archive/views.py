from django.shortcuts import render
from django.http import HttpResponse, HttpRequest


def home(request: HttpRequest) -> HttpResponse:
    return render(request, 'archive/home.html', {'title': 'Home'})
