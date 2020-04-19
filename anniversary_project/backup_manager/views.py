from django.shortcuts import render
from django.http import HttpRequest, HttpResponse


def home(request: HttpRequest) -> HttpResponse:
    return HttpResponse('<h1>Back-up Management Home<h/1>')
