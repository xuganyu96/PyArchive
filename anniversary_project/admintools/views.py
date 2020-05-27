import os
import psutil

from django.http import HttpRequest, Http404
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import AdminTool, AdminToolDeploymentSchema
from .forms import AdminToolForm, AdminToolDeployForm, SystemLogQueryForm
from anniversary_project.settings import BASE_DIR


@user_passes_test(test_func=lambda u: u.is_staff)
@login_required
def home(request: HttpRequest):
    """
    Only serve the admin tools that have been deployed
    """
    admin_tools = AdminTool.objects.filter(is_permanent=True)
    return render(request, "admintools/admintool_home.html", {"admin_tools": admin_tools})


@user_passes_test(test_func=lambda u: u.is_staff)
@login_required
def detail(request: HttpRequest, tool_id: str):
    """
    Serve the AdminTool object to the view.
    """
    #   First check if the tool_id exists; if not, return a 404 error
    if not AdminTool.objects.filter(tool_id=tool_id):
        raise Http404(f"Admin tool {tool_id} does not exist")
    else:
        #   Because tool_id is a primary_key, I can get the instance by using .get
        admintool = AdminTool.objects.get(tool_id=tool_id)
        #   Find the script in scripts/ directory that is the script of this admin tool; we will serve that, as well
        script_text_display = "[ERROR]: Script not found"
        script_text_file_path = os.path.join(BASE_DIR, "scripts", f"{tool_id}.py")
        if os.path.exists(script_text_file_path) and os.path.isfile(
            script_text_file_path
        ):
            with open(script_text_file_path, "r") as f:
                script_text_display = f.read()
        return render(
            request,
            "admintools/admintool_detail.html",
            {"object": admintool, "script_text": script_text_display},
        )


@user_passes_test(test_func=lambda u: u.is_staff)
@login_required
def delete(request: HttpRequest, tool_id: str):
    """
    Given a tool_id, serve the deletion confirmation page
    """
    if not AdminTool.objects.filter(tool_id=tool_id):
        raise Http404(f"Admin tool {tool_id} does not exist")
    else:
        admintool = AdminTool.objects.get(tool_id=tool_id)
        if request.method == "POST":
            if "delete-admintool" in request.POST:
                tool_title = admintool.tool_title
                admintool.delete()
                messages.success(
                    request, f"Admin tool {tool_title} successfully deleted"
                )
                return redirect("admintools-home")
        return render(
            request, "admintools/admintool_confirm_delete.html", {"object": admintool}
        )


@user_passes_test(test_func=lambda u: u.is_staff)
@login_required
def develop(request: HttpRequest):
    """
    If the request.method is POST, then create the admintool instance and save it;
    otherwise, serve the empty form
    """
    if request.method == "POST":
        admin_tool_form = AdminToolForm(request.POST)
        if admin_tool_form.is_valid():
            admin_tool_form.save_with_script(request.POST["script-text"], permanent=True)
            messages.success(request, "New script saved and ready for use")
            return redirect("admintools-home")
    else:
        return render(
            request, "admintools/admintool_develop.html", {"form": AdminToolForm}
        )


@user_passes_test(test_func=lambda u: u.is_staff)
@login_required
def deployment_home(request: HttpRequest):
    """
    :param request:
    :return: Grab all deployments and serve them to home page
    """
    #   Before serving the view, clean out deployments whose PIDs are dead
    for deployment in AdminToolDeploymentSchema.objects.all():
        try:
            p = psutil.Process(deployment.pid)
        except psutil.NoSuchProcess:
            print(f"Deployment {deployment.pk} at {deployment.pid}: {deployment.admintool.tool_title} is dead")
            deployment.delete()

    deployments = AdminToolDeploymentSchema.objects.all()
    return render(request, 'admintools/admintool_deploy_home.html', {'deployments': deployments})


@user_passes_test(test_func=lambda u: u.is_staff)
@login_required
def deployment_create(request: HttpRequest):
    if request.method == "POST":
        admintool_deploy_form = AdminToolDeployForm(request.POST)
        if admintool_deploy_form.is_valid():
            admintool_deploy_form.save()
            admintool_deploy_form.instance.start()
            return redirect("admintools-deploy")
    else:
        form = AdminToolDeployForm()
        return render(
            request, "admintools/admintool_deploy_create.html", {"form": form}
        )


@user_passes_test(test_func=lambda u: u.is_staff)
@login_required
def deployment_delete_confirm(request: HttpRequest, pk: int):
    deployment = AdminToolDeploymentSchema.objects.get(pk=pk)
    if not deployment:
        raise Http404(f"Deployment with id {pk} not found")
    else:
        if request.method == "POST":
            #   The "Yeet" button has been clicked
            deployment.delete()
            return redirect("admintools-deploy")
        else:
            return render(request, 'admintools/admintool_deploy_delete.html', {'object': deployment})


@user_passes_test(test_func=lambda u: u.is_staff)
@login_required
def deployment_system_log(request: HttpRequest):
    """
    :param request:
    :return: serve the entire log
    """
    if request.method == 'POST':
        query_form = SystemLogQueryForm(request.POST)
        if query_form.is_valid():
            max_lines = int(query_form.cleaned_data['max_lines'])

            #   Read the last max_lines of system.log and print
            system_log_path = os.path.join(BASE_DIR, 'log/system.log')
            system_log = "No log found;"
            if os.path.exists(system_log_path) and os.path.isfile(system_log_path):
                with open(system_log_path, 'r') as f:
                    system_log_lines = [line for line in f.read().split('\n') if line != '']
                    start = 0 if len(system_log_lines) < max_lines else max_lines
                    system_log_lines_displayed = system_log_lines[-start:]
                    system_log = '\n'.join(system_log_lines_displayed)

            return render(request, 'admintools/admintool_system_log.html', {'system_log': system_log,
                                                                            'query_form': query_form})
    else:
        return render(request, 'admintools/admintool_system_log.html', {'system_log': '',
                                                                        'query_form': SystemLogQueryForm()})
