import uuid

from boto3.session import Session
from botocore.errorfactory import ClientError


def is_valid_connection_credentials(access_key: str, secret_key: str, region_name: str,
                                    validation_only: bool = True) -> bool:
    """
    :param access_key:
    :param secret_key:
    :param region_name:
    :param validation_only: if True, then after the
    :return: True if and only if a dummy bucket can be created and deleted for this pair of access_key/secret_key in
    this region
    """
    #   Try to create a bucket; if successful, change the instance's is_valid to True
    session = Session(aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key,
                      region_name=region_name)
    s3 = session.client('s3')
    dummy_bucket_name = str(uuid.uuid4())
    try:
        creation_response = s3.create_bucket(Bucket=dummy_bucket_name,
                                             CreateBucketConfiguration={'LocationConstraint': region_name})
        deletion_response = s3.delete_bucket(Bucket=dummy_bucket_name)
        return True
    except Exception as ce:
        return False
