import os
import urllib.parse
from datetime import datetime, timezone

import boto3

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

TABLE_NAME = os.environ["TABLE_NAME"]

def iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def _extract_s3_targets(event: dict):
    """
    Supports:
      1) S3 notification events: {"Records":[{"s3":{...}}]}
      2) EventBridge S3 events: {"detail": {"bucket": {"name": ...}, "object": {"key": ...}}}
    Returns: list of (bucket, key)
    """
    targets = []

    # Case 1: S3 Notification
    records = event.get("Records")
    if isinstance(records, list) and records:
        for record in records:
            s3info = record.get("s3", {})
            bucket = s3info.get("bucket", {}).get("name")
            key = s3info.get("object", {}).get("key")
            if bucket and key:
                targets.append((bucket, key))
        return targets

    # Case 2: EventBridge
    detail = event.get("detail") or {}
    bucket = (detail.get("bucket") or {}).get("name")
    key = (detail.get("object") or {}).get("key")
    if bucket and key:
        targets.append((bucket, key))

    return targets

def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)

    targets = _extract_s3_targets(event)

    for bucket, key in targets:
        key = urllib.parse.unquote_plus(key)

        head = s3.head_object(Bucket=bucket, Key=key)

        size_bytes = int(head.get("ContentLength", 0))
        etag = head.get("ETag", "").strip('"')
        content_type = head.get("ContentType", "application/octet-stream")
        last_modified = head.get("LastModified")
        ingested_at = iso_utc(last_modified if last_modified else datetime.now(timezone.utc))

        # x-amz-meta-sourcesystem -> boto3: Metadata keys become lowercase
        user_meta = head.get("Metadata", {}) or {}
        source_system = user_meta.get("sourcesystem", "unknown")

        sk = f"{ingested_at}#{key}"
        gsi1pk = bucket
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
