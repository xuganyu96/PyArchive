import os

from django.http import HttpRequest, Http404
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import AdminTool
from .forms import AdminToolForm
from anniversary_project.settings import BASE_DIR


@user_passes_test(test_func=lambda u: u.is_staff)
@login_required
def home(request: HttpRequest):
    """
    Only serve the admin tools that have been deployed
    """
    admin_tools = AdminTool.objects.filter(is_permanent=True)
    return render(request, "admintools/home.html", {"admin_tools": admin_tools})


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
