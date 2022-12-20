import boto3
from boto3.session import Session
from botocore.exceptions import ClientError
import os
from os.path import join
import urllib

download_dir = '/tmp/downloads/'
s3 = boto3.resource('s3')

import json

from os import mkdir
import shutil

print('Loading function...')

SOURCE_EMAIL = os.environ['SOURCE_ADDRESS']

def setup_ses_client():
    """Creates an SES client

    return:
        An SES client
    """
    session = Session()
    return session.client('ses')

def send_message(email_object, client, bucket, file, recipient_emails):
    print("File: {}, Bucket: {}, Recipients: {}".format(file, bucket, recipient_emails))
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Source='{}'.format(SOURCE_EMAIL),
            Destination={
                'ToAddresses': recipient_emails
            },
            Message={
                'Subject': {
                    'Data': email_object['subject'],
                },
                'Body': {
                    'Text': {
                        'Data': email_object['message'],
                    },
                }
            },
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print('[ERROR]: ', e.response)
        return e.response
    else:
        print(response)
        return response


def build_email_object(file):
    file_no_path = file.rsplit('/', 1)[-1]
    subject = os.environ['SUBJECT']

    body = os.environ['BODY']
    email_object = {
        'subject': subject,
        'message': body.format(
            file=file_no_path
        )
    }
    return email_object


def extract_s3_event(event):
    s3event = event['Records'][0]['s3']
    fileUploadedTo = s3event['bucket']['name']
    fileUploaded = urllib.parse.unquote(s3event['object']['key'])
    user = fileUploaded.split('/')[0]
    eventName = event['Records'][0]['eventName']
    size = s3event['object']['size']
    print("eventName: {}, bucket: {}, key: {}, size: {}".format(eventName, fileUploadedTo, fileUploaded, size))
    return fileUploadedTo, fileUploaded, user, size

def get_emails_from_bucket_tags(bucket):
    session = Session()
    response = session.client('s3').get_bucket_tagging(
        Bucket=bucket
    )
    keys = response.get('TagSet')
    recipient_emails = []

    for x in keys:
        prefix = x.get('Key').lower()
        if prefix.startswith('email'):
            recipient_emails.append(x.get('Value'))

    return recipient_emails

# user/uploads/blank7.csv => blank7.csv
def trim_path_to_filename(path) :
    if path.rfind('/') != -1:
        path = path[path.rfind('/')+1:len(path)]
    return path

# user/uploads/blank7.csv => blank7.csv
def trim_path_to_dir(path) :
    if path.rfind('/') != -1:
        path = path[0:path.rfind('/')+1]
    return path

def download_file(bucket, file):
    session = Session()
    download_filename = trim_path_to_filename(file)
    print("download_filename: {}".format(download_filename))
    download_path = join(download_dir, download_filename)
    print('downloading {0}/{1} to {2}'.format(bucket, file, download_path))
    session.client('s3').download_file(bucket, file, download_path)
    return download_path

def reset_folder():
    print('Deleting local contents of {}'.format(download_dir))
    if os.path.exists(download_dir):
        shutil.rmtree(download_dir)
    mkdir(download_dir)

def get_everything_after_last_slash(path) :
    if ( path.rfind('/') != -1 ) :
        path = path[path.rfind('/')+1:len(path)]
    return path

def get_everything_before_last_slash(path) :
    if ( path.rfind('/') != -1 ) :
        path = path[0:path.rfind('/')]
    return path


def lambda_handler(event, context):
    """
    Takes an incoming S3 event and builds an email object to send through SES
    :param event:
    :param context:
    :return:
    """

    reset_folder()

    json_event = json.dumps(event)

    bucket, file, user, size = extract_s3_event(event)

    recipient_emails = get_emails_from_bucket_tags(bucket)
    # print("File: {}, Bucket: {}".format(file, bucket))
    file = file.replace("+", " ")

    parent_directory_path = get_everything_before_last_slash(file)
    parent_directory_only = get_everything_after_last_slash(parent_directory_path)

    # early exit if this represents a folder
    if file.endswith("/"):
        print("Skipping folder: {}".format(file))
        return {
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': "Skipping folder: {}".format(file)
        }
    elif not size:
        print("Skipping empty file: {} of size: {}".format(file, size))
        return {
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': "Skipping empty file: {}".format(file)
        }
    else:
        email_object = build_email_object(file)
        status = send_message(email_object, setup_ses_client(), bucket, file, recipient_emails)
        body = 'Email sent! Message ID: {}'.format(status['MessageId']) if status['ResponseMetadata'][
                                                                           'HTTPStatusCode'] == 200 else \
        status['Error']['Message']
        return {
            'statusCode': status['ResponseMetadata']['HTTPStatusCode'],
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': body
        }

    reset_folder()
