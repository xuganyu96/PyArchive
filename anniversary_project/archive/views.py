from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from django.contrib.auth.decorators import login_required


#   TODO:
#   Home should be made login only, and should only display the archives created by the user currently logged in
@login_required
def home(request: HttpRequest) -> HttpResponse:
    cur_user = request.user
    return render(request,
                  'archive/home.html',
                  context={'title': 'Home'})
