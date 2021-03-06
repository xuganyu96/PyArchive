import os

from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, HttpRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Archive, ArchivePartMeta
from .forms import ArchiveForm
from .utils import queue_archive_caching, can_uncache, uncache


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
            return redirect(reverse('archive-detail', kwargs={'pk': form.instance.archive_id}))
    else:
        form = ArchiveForm()

    return render(request, 'archive/archive_form.html',
                  context={'title': 'Create new archive',
                           'form': form})


class ArchiveDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Archive

    def get_context_data(self, **kwargs):
        """
        :param kwargs:
        :return: Overwrite this method to provide additional context variables to the archive_detail.html template
        """
        # Call the base implementation first to get a context
        archive = self.get_object()
        context = super().get_context_data(**kwargs)

        context['parts'] = ArchivePartMeta.objects.filter(archive=self.get_object())
        context['can_uncache'] = can_uncache(archive)
        return context

    def test_func(self):
        """
        :return: Only allow user to pass if user is the owner
        """
        archive = self.get_object()
        return archive.owner == self.request.user

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        archive = self.get_object()
        if 'cache_archive' in request.POST:
            #   If the POST request is for caching an archive, then queue download jobs and display success message
            queue_archive_caching(archive)
            messages.success(request, 'Caching jobs queued for this archive')
            return redirect(reverse('archive-detail', kwargs={'pk': archive.archive_id}))
        elif 'uncache_archive' in request.POST:
            #   If the POST request is for uncaching an archive, then check if it can be uncached. An Archive can be
            #   un-cached if and only if all of its parts are online
            if can_uncache(archive):
                uncache(archive)
            else:
                messages.warning(request, 'Archive is not remotely backed up fully')
            return redirect(reverse('archive-detail', kwargs={'pk': archive.archive_id}))

        else:
            messages.warning(request, 'invalid action!')
            return redirect(reverse('archive-detail', kwargs={'pk': archive.archive_id}))


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
