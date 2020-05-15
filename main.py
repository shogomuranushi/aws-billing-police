import boto3
import json
import logging
import os
import sys

from base64 import b64decode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from decimal import *

SLACK_CHANNEL     = os.environ['SLACK_CHANNEL']
SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']
AWS_ACCOUNT_NAME       = os.environ['AWS_ACCOUNT_NAME']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ce = boto3.client('ce')

def lambda_handler(event, context):
    logger.info("Event: %s", str(event))

    # cron(30 0 * * ? *) by GMT
    # Output the amount of AWS usage 2 days ago because it takes a long time to aggregate on the AWS side.
    start = date.today() - timedelta(days=2)
    end = date.today() - timedelta(days=1)

    fields = []
    total  = Decimal(0)

    ce_res = ce.get_cost_and_usage(
        TimePeriod = {
            'Start': str(start),
            'End'  : str(end)
        },
        Granularity = 'DAILY',
        Metrics     = ['UnblendedCost'],
        GroupBy     = [{
            'Type': 'DIMENSION',
            'Key' : 'SERVICE'
        }]
    )
    logger.info("CostAndUsage: %s", str(ce_res))

    rbt = ce_res['ResultsByTime']
    for groups in rbt:
        for group in groups['Groups']:
            # The dollar-yen exchange rate is 110 yen.
            # If you want to use something other than Japanese yen, please correct this.
            value = round(Decimal(group["Metrics"]["UnblendedCost"]["Amount"]) * 110, 0)
            # Because of the large amount of information, items under 2 yen have been omitted.
            # If you want to use something other than Japanese yen, please correct this.
            if value >= 2:
                print(value)
                fields.append({
                    "title": group["Keys"][0],
                    # If you want to use something other than Japanese yen, please correct this.
                    "value": ":yen: " + str("{:,}".format(value)) + "円",
                    "short": True
                })
                total += Decimal(group["Metrics"]["UnblendedCost"]["Amount"])
            else:
                # If you want to use something other than Japanese yen, please correct this.
                logger.info("Event: %s is under 1 yen", group["Keys"][0])
    
    # If you want to use something other than Japanese yen, please modify the pretext.
    slack_message = {
        "attachments": [
            {
                'fallback'   : "Required plain-text summary of the attachment.",
                'color'      : "#36a64f",
                'author_name': ":male-police-officer: :moneybag: Billing 警察",
                'author_link': "http://flickr.com/bobby/",
                'author_icon': "http://flickr.com/icons/bobby.jpg",
                'text'       : " ",
                'fields'     : fields,
                'image_url'  : "http://my-website.com/path/to/image.jpg",
                'thumb_url'  : "http://example.com/path/to/thumb.png",
                'footer'     : "Powered by on %s Virginia Lambda" % (str(AWS_ACCOUNT_NAME)),
                'footer_icon': "https://platform.slack-edge.com/img/default_application_icon.png",
                'pretext'    : "* %s の [ %s ] のAWS利用料 は :money_with_wings: %s 円です*" % (str(start), str(AWS_ACCOUNT_NAME), str("{:,}".format(round(total * 110, 0)))),
                'channel'    : SLACK_CHANNEL
            }
        ]
    }

    req = Request(SLACK_WEBHOOK_URL, json.dumps(slack_message).encode('utf-8'))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted to %s", slack_message['attachments'][0]['channel'])
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)
