from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, HttpRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Archive


@login_required
def home(request: HttpRequest) -> HttpResponse:
    cur_user = request.user
    user_archives = Archive.objects.filter(owner=cur_user).order_by('-date_created')

    return render(request,
                  'archive/home.html',
                  context={'title': 'Home',
                           'archives': user_archives})


class ArchiveDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Archive

    def test_func(self):
        """
        :return: Only allow user to pass if user is the owner
        """
        archive = self.get_object()
        return archive.owner == self.request.user


class ArchiveCreateView(LoginRequiredMixin, CreateView):
    model = Archive
    fields = ['archive_file', 'archive_name']

    def form_valid(self, form):
        #   Overwrite the form validation method for filling in archive owner information
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ArchiveUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Archive
    fields = ['archive_name']

    def test_func(self):
        """
        :return: Only allow user to pass if user is the owner
        """
        archive = self.get_object()
        return archive.owner == self.request.user


class ArchiveDeleteview(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Archive

    def test_func(self):
        """
        :return: Only allow user to pass if user is the owner
        """
        archive = self.get_object()
        return archive.owner == self.request.user

    def get_success_url(self):
        return reverse('archive-home')
