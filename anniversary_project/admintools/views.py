from django.shortcuts import render

from .models import AdminTool


def home(request):
    """
    Only serve the admin tools that have been deployed
    """
    admin_tools = AdminTool.objects.filter(deployed=True)
    return render(request, 'admintools/home.html', {'admin_tools': admin_tools})


def detail(request, tool_id: str):
    return render(request, 'admintools/admintool_detail.html')


def develop(request):
    return render(request, 'admintools/admintool_develop.html')


def deploy(request):
    return render(request, 'admintools/admintool_deploy.html')
