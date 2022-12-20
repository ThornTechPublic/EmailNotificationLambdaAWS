# README

## Background

This is the Email Alert Add-on, which sends email notifications when files are uploaded to S3.

Instructions for using this solution are on https://www.thorntech.com/blog. 

Briefly, this solution uses a SAM template to deploy a Lambda (Python) that sends emails via SES. You wire S3 events to the Lambda to trigger an email. The email recipient comes from a tag on the S3 bucket.

## Deployment

To install this Email Notification Lambda:

```bash 
python deploy.py [ --profile default --region us-east-1 --email no-reply@example.com --project email-notification-lambda --codebucket email-notification-lambda-sam]
```

Instead of supplying all of these arguments, it's easier to edit the default arguments in `deploy.py`.

The `--email` parameter is the source email address. Make sure that this is email is valid.

## Configuration

You will need to verify the source and recipient email addresses in SES. This involves clicking a confirmation link sent by SES.

If you have a lot of customers that need to receive email, you might consider taking SES out of sandbox mode. This involves contacting SES, and filling out a questionnaire about your email volume and frequency.



