import argparse
import boto3
import os

def create_deployment_bucket(bucket, profile, region):
    session = boto3.Session(profile_name=profile)
    s3 = session.client('s3')
    try:
        s3.head_bucket(Bucket=bucket)
        return
    except:
        if region == "us-east-1":
            response = s3.create_bucket(Bucket=bucket)
        else:
            response = s3.create_bucket(Bucket=bucket,CreateBucketConfiguration={'LocationConstraint': region})
        return response


def build():
    # Build the Lambda deployment packages
    os.system('sam build -b build/')


def package(bucket, profile):
    # generate next stage yaml file
    os.system('sam package                       \
        --template-file build/template.yaml      \
        --output-template-file build/output.yaml \
        --s3-bucket {bucket}                     \
        --profile {profile}'.format(bucket=bucket, profile=profile)
    )


def deploy(project, profile, region, source_email):
    # the actual deployment step
    os.system('sam deploy                         \
        --template-file build/output.yaml         \
        --stack-name {project}                    \
        --capabilities CAPABILITY_NAMED_IAM       \
        --profile {profile}                       \
        --region {region}                        \
        --parameter-overrides SourceEmail={source_email}'.format(
                project=project,
                profile=profile,
                region=region,
                source_email=source_email
            )
    )



def parse_args(args=None):
    des = "Deploys the File Uploaded Email Notification Lambda"
    parser = argparse.ArgumentParser(description=des)
    parser.add_argument(
        '--profile',
        '-p',
        help="Specify an AWS profile",
        type=str,
        default='default'
    )
    parser.add_argument(
        '--region',
        '-r',
        help="Specify the AWS region",
        type=str,
        default='us-east-1'
    )
    parser.add_argument(
        '--email',
        help="Specify the sender email address",
        type=str,
        default='robert.chen@thorntech.com'
    )
    parser.add_argument(
        '--project',
        help="Specify the project name",
        type=str,
        default='email-notification-lambda'
    )
    parser.add_argument(
        '--codebucket',
        help="Specify the deployment S3 bucket",
        type=str,
        default='email-notification-lambda-sam'
    )
    return parser.parse_args(args)

def clean_build(target):
    if os.path.exists(target):
        for d in os.listdir(target):
            try:
                clean_build('{}/{}'.format(target, d))
            except OSError:
                os.remove('{}/{}'.format(target, d))
        os.rmdir(target)


def main(args=None):
    args = parse_args(args)
    PROFILE = args.profile
    REGION = args.region
    SOURCE_EMAIL = args.email
    PROJECT = args.project

    # Bucket used to stage lambda code
    BUCKET = args.codebucket

    print("REGION: {}".format(REGION))
    print("PROFILE: {}".format(PROFILE))
    print("SOURCE_EMAIL: {}".format(SOURCE_EMAIL))
    print("PROJECT: {}".format(PROJECT))
    print("BUCKET: {}".format(BUCKET))

    # Create the deployment bucket if it does not exist
    create_deployment_bucket(BUCKET, PROFILE, REGION)

    # Clean and recreate the build directory
    clean_build('build')
    os.mkdir('build')

    print('Building...')
    build()
    print('Build complete...')

    print('Packaging...')
    package(BUCKET, PROFILE)
    print('Packaging complete...')

    print('Deploying...')
    deploy(PROJECT, PROFILE, REGION, SOURCE_EMAIL)
    print('Deployment complete.')


if __name__ == "__main__":
    main()
