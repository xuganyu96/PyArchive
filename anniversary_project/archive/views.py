import os

from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, HttpRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Archive
from .forms import ArchiveForm
from .portal_utils import schedule_archive_upload


@login_required
def home(request: HttpRequest) -> HttpResponse:
    cur_user = request.user
    user_archives = Archive.objects.filter(owner=cur_user).order_by('-date_created')

    return render(request,
                  'archive/home.html',
                  context={'title': 'Home',
                           'archives': user_archives})


@login_required
def create(request: HttpRequest) -> HttpResponse:
    cur_user = request.user

    if request.method == "POST":
        form = ArchiveForm(request.POST, request.FILES)
        form.instance.owner = cur_user
        if form.is_valid():
            form.save()
            schedule_archive_upload(archive=form.instance)
            return redirect(reverse('archive-detail', kwargs={'pk': form.instance.archive_id}))
    else:
        form = ArchiveForm()

    return render(request, 'archive/archive_form.html',
                  context={'title': 'Create new archive',
                           'form': form})


class ArchiveDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Archive

    def test_func(self):
        """
        :return: Only allow user to pass if user is the owner
        """
        archive = self.get_object()
        return archive.owner == self.request.user


class ArchiveUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Archive
    fields = ['archive_name']

    def test_func(self):
        """
        :return: Only allow user to pass if user is the owner
        """
        archive = self.get_object()
        return archive.owner == self.request.user


class ArchiveDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Archive

    def test_func(self):
        """
        :return: Only allow user to pass if user is the owner
        """
        archive = self.get_object()
        return archive.owner == self.request.user

    def get_success_url(self):
        return reverse('archive-home')
