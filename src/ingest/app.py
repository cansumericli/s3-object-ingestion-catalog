import os
import urllib.parse
from datetime import datetime, timezone

import boto3

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

TABLE_NAME = os.environ["TABLE_NAME"]

def iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def lambda_handler(event, context):
    """
    Trigger: S3 ObjectCreated events.
    Action: Read S3 object attributes + optional custom metadata and write a catalog record to DynamoDB.
    """

    table = dynamodb.Table(TABLE_NAME)

    for record in event.get("Records", []):
        s3info = record.get("s3", {})
        bucket = s3info.get("bucket", {}).get("name")
        key = s3info.get("object", {}).get("key")

        if not bucket or not key:
            continue

        key = urllib.parse.unquote_plus(key)

        # Read technical attributes + x-amz-meta-* custom metadata
        head = s3.head_object(Bucket=bucket, Key=key)

        size_bytes = int(head.get("ContentLength", 0))
        etag = head.get("ETag", "").strip('"')
        content_type = head.get("ContentType", "application/octet-stream")
        last_modified = head.get("LastModified")
        ingested_at = iso_utc(last_modified if last_modified else datetime.now(timezone.utc))

        # Optional custom metadata that uploader can set: x-amz-meta-sourcesystem
        user_meta = head.get("Metadata", {}) or {}
        source_system = user_meta.get("sourcesystem", "unknown")  # PK

        # Keys for DynamoDB
        sk = f"{ingested_at}#{key}"          # sort key (time-ordered per source)
        gsi1pk = bucket                      # for bucket/time range queries
        gsi1sk = f"{ingested_at}#{source_system}#{key}"

        item = {
            "sourceSystem": source_system,
            "sk": sk,
            "gsi1pk": gsi1pk,
            "gsi1sk": gsi1sk,
            "bucket": bucket,
            "objectKey": key,
            "s3Uri": f"s3://{bucket}/{key}",
            "ingestedAt": ingested_at,
            "sizeBytes": size_bytes,
            "etag": etag,
            "contentType": content_type,
            "status": "INGESTED",
        }

        table.put_item(Item=item)

    return {"statusCode": 200, "body": "ok"}
