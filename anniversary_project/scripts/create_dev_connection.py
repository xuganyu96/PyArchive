import os

from s3connections.models import S3Connection


def run(logger=print):
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    logger(access_key, secret_key)
    dev_conn = S3Connection(
        connection_name='dev-connection',
        access_key=access_key,
        secret_key=secret_key,
        region_name='us-west-2',
        is_valid=True,
        is_active=True
    )
    s3 = dev_conn.get_client('s3')
    logger(f'dev bucket named is {dev_conn.connection_id}')
    s3.create_bucket(Bucket=str(dev_conn.connection_id),
                     CreateBucketConfiguration={'LocationConstraint': dev_conn.region_name})
    dev_conn.save()
