# S3 Object Ingestion Catalog

Event-driven serverless catalog that tracks S3 object ingestion events and indexes object metadata in DynamoDB (IaC via AWS SAM).

## What it does
- Upload a file to an S3 bucket
- S3 event triggers a Lambda ingestion function
- Lambda reads object attributes (size, content-type, etag, last-modified) + optional custom metadata
- Stores a queryable “catalog record” in DynamoDB

## Architecture
S3 (ObjectCreated) -> Lambda (ingest) -> DynamoDB (catalog/index) -> (optional) API Gateway + Lambda (query)

## Roadmap (V2)
- Generate **pre-signed download URLs** for private objects
- Additional indexes for filtering (contentType, status, sourceSystem)
- Optional analytics layer (Athena/QuickSight)
