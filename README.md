# AWS Billing Police

This is a tool that posts your AWS usage to Slack every day.

It's designed to increase cost awareness by looking at your daily AWS usage.

The python code is very simple, about 100 lines, and even including serverless.yaml, it is less than 150 lines in total.

![sample](images/sample_image.png)

## Architecure

Start Lambda at the time specified in the CloudWatch Event and post the Slack channel.

![image](images/archtecture.png)

## Setup

1. Getting the Webhook URL for Slack

    Please refer to the following URL -> [https://slack.com/help/articles/115005265063-Incoming-Webhooks-for-Slack](https://slack.com/help/articles/115005265063-Incoming-Webhooks-for-Slack)

2. Putting Slack's Webhook URL into the AWS Parameter Store

    ```:bash
    aws ssm put-parameter --region us-east-1 \
        --name "SLACK_WEBHOOK_URL" \
        --description "Slack Webhook URL" \
        --type "String" \
        --value "https://hooks.slack.com/services/xxxxx/xxxxx/xxxxx"
    ```

3. Update files under /env

    ```:bash
    vim ./env/dev.yaml
    ```

4. Deploy

    ```:bash
    make dev
    ```

## Premise

- Output the amount of AWS usage 2 days ago because it takes a long time to aggregate on the AWS side.
- It's converted from dollars to Japanese yen.
  - If you would like to use a currency other than Japanese Yen, please change the "If you want to use something other than Japanese yen" in the main.py.
