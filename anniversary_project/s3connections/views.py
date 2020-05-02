from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from boto3.session import Session

from .forms import S3ConnectionCreateForm
from .models import S3Connection
from s3connections.utils import is_valid_connection_credentials


@login_required
def home(request) -> HttpResponse:
    connections = S3Connection.objects.order_by('-is_active').all()

    return render(request,
                  's3connections/home.html',
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

        return render(request, 's3connections/create.html', {'form': s3_conn_create_form})
    else:
        messages.error(request, 'Only admin users can make changes to S3 connections')
        return redirect('s3-connection-home')


def detail(request: HttpRequest, pk) -> HttpResponse:
    """
    :param pk:
    :param request:
    :return:
    """
    connection: S3Connection = S3Connection.objects.get(pk=pk)

    if request.method == "POST":
        if 'validate' in request.POST:
            #   Check if the connection is a valid one and update its is_valid attribute
            #   If yes, print a success message; if no, print an error message
            is_valid = is_valid_connection_credentials(access_key=connection.access_key,
                                                       secret_key=connection.secret_key,
                                                       region_name=connection.region_name)
            connection.is_valid = is_valid
            connection.save()
            if is_valid:
                messages.success(request, message='Connection successfully validated')
            else:
                messages.warning(request, message='Connection validation failed; marking connection invalid')
        elif 'make_active' in request.POST:
            #   Check if the connection.is_valid
            #   If yes, then set this connection to be is_active, and set all other connections' is_active to False
            #   If no, then don't do anything except for posting a warning message
            if connection.is_valid:
                for other_conn in S3Connection.objects.all():
                    other_conn.is_active = False
                    other_conn.save()
                connection.is_active = True
                connection.save()
                messages.success(request, message='Connection successfully activated')
            else:
                messages.warning(request, message='Connection is not valid; validate it first')

        return redirect(reverse('s3-connection-detail', kwargs={'pk': pk}))
    else:
        #   The user is just viewing things
        return render(request, 's3connections/s3connection_detail.html',
                      context={'object': connection})


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
