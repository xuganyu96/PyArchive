from django.shortcuts import render


def home(request):
    return render(request, 'admintools/home.html')


def detail(request, tool_id: str):
    return render(request, 'admintools/admintool_detail.html')


def develop(request):
    return render(request, 'admintools/admintool_develop.html')


def deploy(request):
    return render(request, 'admintools/admintool_deploy.html')
