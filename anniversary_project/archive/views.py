from django.shortcuts import render
from django.http import HttpResponse, HttpRequest


def home(request: HttpRequest) -> HttpResponse:
    return HttpResponse('<h1>Home page</h1>')
