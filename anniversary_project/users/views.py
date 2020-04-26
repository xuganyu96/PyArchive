from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm


def register(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        user_creation_form = UserRegisterForm(request.POST)
        if user_creation_form.is_valid():
            #   Save the newly created user
            user_creation_form.save()

            #   Display a flash message for user creation
            username = user_creation_form.cleaned_data.get('username')
            messages.success(request, f"user {username} created")

            #   After user creation, redirect to archive-home page
            return redirect('login')
    else:
        user_creation_form = UserRegisterForm()

    return render(request, 'users/register.html', {'user_creation_form': user_creation_form})


@login_required
def profile(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        #   Save data if and only if BOTH of the forms were valid
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            messages.success(request, "Account profile successfully updated")
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'users/profile.html',
                  context={'user_form': user_form,
                           'profile_form': profile_form})
