from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from boto3.session import Session

from .forms import S3ConnectionCreateForm
from .models import S3Connection


@login_required
def home(request) -> HttpResponse:
    connections = S3Connection.objects.all()

    return render(request,
                  's3portal/home.html',
                  context={'title': 'S3 Connections Home',
                           'connections': connections})


@login_required
def create(request) -> HttpResponse:
    can_create = request.user.is_staff
    if can_create:
        if request.method == 'POST':
            s3_conn_create_form = S3ConnectionCreateForm(request.POST)
            if s3_conn_create_form.is_valid():
                #   Try to create a bucket; if successful, change the instance's is_valid to True
                session = Session(aws_access_key_id=s3_conn_create_form.instance.access_key,
                                  aws_secret_access_key=s3_conn_create_form.instance.secret_key,
                                  region_name=s3_conn_create_form.instance.region_name)
                s3 = session.client('s3')
                try:
                    response = s3.create_bucket(Bucket=str(s3_conn_create_form.instance.connection_id),
                                                CreateBucketConfiguration={
                                                    'LocationConstraint': s3_conn_create_form.instance.region_name
                                                })
                    s3_conn_create_form.instance.is_valid = True
                except Exception as e:
                    pass
                finally:
                    s3_conn_create_form.save()

                #   Display a flash message for connection creation
                connection_name = s3_conn_create_form.cleaned_data.get('connection_name')
                if s3_conn_create_form.instance.is_valid:
                    messages.success(request, f"S3 connection {connection_name} created")
                else:
                    messages.error(request, f"S3 connection {connection_name} cannot be validated")

                #   After user creation, redirect to archive-home page
                return redirect('s3-connection-home')
        else:
            s3_conn_create_form = S3ConnectionCreateForm()

        return render(request, 's3portal/create.html', {'form': s3_conn_create_form})
    else:
        messages.error(request, 'Only admin users can make changes to S3 connections')
        return redirect('s3-connection-home')


class S3ConnectionDetailView(LoginRequiredMixin, DetailView):
    model = S3Connection


class S3ConnectionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = S3Connection
    fields = ['connection_name']

    def test_func(self):
        """
        :return: Only allow user to pass if user is the owner
        """
        return self.request.user.is_staff


class S3ConnectionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = S3Connection

    def test_func(self):
        """
        :return: Only allow user to pass if user is the owner
        """
        return self.request.user.is_staff

    def get_success_url(self):
        return reverse('s3-connection-home')
