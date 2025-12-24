import os
import json

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["TABLE_NAME"]

def _dumps(obj):
    return json.dumps(obj, default=str)

def lambda_handler(event, context):
    """
    API:
      GET /sources/{sourceSystem}/objects
      GET /objects?bucket=...&start=...&end=...
    """
    table = dynamodb.Table(TABLE_NAME)

    path_params = event.get("pathParameters") or {}
    source_system = path_params.get("sourceSystem")

    # 1) Query by source system (PK)
    if source_system:
        resp = table.query(
            KeyConditionExpression=Key("sourceSystem").eq(source_system),
            ScanIndexForward=False,  # newest first (because SK starts with timestamp)
        )
        return {
            "statusCode": 200,
            "headers": {"content-type": "application/json"},
            "body": _dumps(resp.get("Items", [])),
        }

    # 2) Query by bucket + date range (GSI1)
    qs = event.get("queryStringParameters") or {}
    bucket = qs.get("bucket")
    start = qs.get("start")
    end = qs.get("end")

    if not (bucket and start and end):
        return {
            "statusCode": 400,
            "headers": {"content-type": "application/json"},
            "body": _dumps({"error": "Provide bucket, start, end. Example: /objects?bucket=...&start=...&end=..."}),
        }

    # We stored:
    #   gsi1pk = bucket
    #   gsi1sk = "{ingestedAt}#{sourceSystem}#{objectKey}"
    resp = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("gsi1pk").eq(bucket) & Key("gsi1sk").between(f"{start}#", f"{end}~"),
        ScanIndexForward=True,
    )

    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": _dumps(resp.get("Items", [])),
    }
