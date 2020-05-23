import uuid
from boto3.session import Session

from django.urls import reverse
from django.db import models

REGION_NAMES = [('us-west-2', 'us-west-2')]


class S3Connection(models.Model):
    """
    Simple model for storing AWS access key and secret keys;
    TODO: Implement secret key hashing
    """

    #   Connection ID will also be bucket name
    connection_id = models.CharField(max_length=64, default=uuid.uuid4, primary_key=True)
    connection_name = models.CharField(max_length=512, default=uuid.uuid4)
    access_key = models.CharField(max_length=256, null=False)
    secret_key = models.CharField(max_length=256, null=False)
    region_name = models.CharField(max_length=64, choices=REGION_NAMES, default='us-west-2')
    is_valid = models.BooleanField(default=False, null=False)
    #   There can be exactly one entry in S3Connection whose is_active is True
    is_active = models.BooleanField(default=False, null=False)

    def __str__(self):
        return self.connection_name

    #   Define the method for returning the URL of specific archive's detail page
    def get_absolute_url(self):
        return reverse('s3-connection-detail', kwargs={'pk': self.connection_id})

    def get_client(self, service_name):
        session = Session(aws_access_key_id=str(self.access_key),
                          aws_secret_access_key=str(self.secret_key),
                          region_name=str(self.region_name))
        return session.client(service_name)

    def get_resource(self, service_name):
        session = Session(aws_access_key_id=str(self.access_key),
                          aws_secret_access_key=str(self.secret_key),
                          region_name=str(self.region_name))
        return session.resource(service_name)

    def delete(self, using=None, keep_parents=False):
        """
        Overwrite the default delete method so the bucket would be deleted when the model instance is deleted
        """
        try:
            session = Session(
                aws_access_key_id=str(self.access_key),
                aws_secret_access_key=str(self.secret_key),
                region_name=str(self.region_name)
            )
            s3 = session.client('s3')
            response = s3.delete_bucket(Bucket=self.connection_id)
        except Exception as e:
            pass
        super().delete()

