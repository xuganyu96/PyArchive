from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import AdminTool
from .forms import AdminToolForm


def home(request: HttpRequest):
    """
    Only serve the admin tools that have been deployed
    """
    admin_tools = AdminTool.objects.filter(deployed=True)
    return render(request, 'admintools/home.html', {'admin_tools': admin_tools})


def detail(request, tool_id: str):
    return render(request, 'admintools/admintool_detail.html')


def develop(request: HttpRequest):
    """
    If the request.method is POST, then create the admintool instance and save it;
    otherwise, serve the empty form
    """
    if request.method == 'POST':
        admin_tool_form = AdminToolForm(request.POST)
        if admin_tool_form.is_valid():
            admin_tool_form.save_with_script(request.POST['script-text'], deploy=True)
            messages.success(request, "New script saved and ready for use")
            return redirect('admintools-home')
    else:
        return render(request, 'admintools/admintool_develop.html', {'form': AdminToolForm})


def deploy(request: HttpRequest):
    return render(request, 'admintools/admintool_deploy.html')
