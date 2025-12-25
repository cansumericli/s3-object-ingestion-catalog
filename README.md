# 📦 S3 Object Ingestion Catalog

A simple, event-driven AWS serverless application that ingests **S3 object metadata** into a **queryable DynamoDB catalog** and exposes APIs for object discovery.

This project focuses on **clarity, real-world patterns, and scalability**, not over-engineering.

---

## 🧠 Overview

Amazon S3 is great for storing files, but it does not provide a **searchable catalog** of objects.

This project adds a lightweight **catalog layer** on top of S3 using AWS managed services:

- **Amazon S3** for object storage  
- **Amazon EventBridge** for event routing  
- **AWS Lambda** for ingestion and querying  
- **Amazon DynamoDB** for indexing and fast lookups  
- **Amazon API Gateway (HTTP API)** for access  

The result is a system where S3 objects become **discoverable, queryable, and API-accessible**.

---

## 🎯 Motivation

S3 object metadata exists, but it is stored **per object** and can only be retrieved when the object key is already known.

Amazon S3 excels at storing objects but lacks built-in searchability. Without a catalog layer:

❌ No way to query objects by metadata across buckets
❌ Cannot filter by source system, tags, or time ranges
❌ Must know exact object keys to retrieve metadata
❌ Difficult to build discovery APIs on top of S3

Result: S3 becomes a black box where data exists but isn't easily discoverable.

## ✨ The Solution
This project adds an automated catalog layer that makes S3 objects:

Discoverable - Query across all objects instantly
Indexed - Sub-100ms lookups via DynamoDB
API-accessible - REST endpoints for programmatic access
Event-driven - Zero polling, real-time ingestion

This turns S3 from a simple object store into a **discoverable data platform**.

---

## 🏗️ High-Level Architecture

*(Diagram created in Canva)*


```markdown
![Architecture Diagram](./docs/architecture.png)
```

---

## 🔄 Architecture Flow

1. A file is uploaded to the S3 bucket  
2. S3 emits an **Object Created** event to EventBridge  
3. EventBridge triggers the **Ingest Lambda**  
4. The Lambda:
   - reads system and user-defined metadata
   - enriches it with ingestion context
   - writes a catalog record into DynamoDB  
5. A **Query Lambda** exposes read APIs via HTTP API  

All components are **fully serverless**.

---

## 🗂️ Data Model (DynamoDB)

**Table:** `s3-object-ingestion-catalog-table`

### Primary Key
- **PK:** `sourceSystem`
- **SK:** `timestamp#objectKey`

This allows fast queries like:
> *Show me all objects ingested by source X*

### Global Secondary Index (GSI1)
- **GSI1PK:** `bucket`
- **GSI1SK:** `timestamp#sourceSystem#objectKey`

This supports:
> *Show me all objects in this bucket between two dates*

---

## 🔍 Supported Query Patterns

- Objects by **source system**
- Objects by **bucket + date range**
- Results sorted by ingestion time

All queries are **index-based** (no scans).

---

## 🚀 Deployment

### Prerequisites
- AWS CLI configured
- AWS SAM CLI installed
- Python 3.12

### Build and deploy
```bash
sam build
sam deploy
```

This deploys:
- S3 bucket
- DynamoDB table
- EventBridge rule
- Two Lambda functions
- HTTP API

---

## 🧪 Testing

### Upload a test object
```bash
aws s3 cp ./README.md \
  s3://<UPLOAD_BUCKET>/test/readme-test.txt \
  --metadata sourcesystem=cli-test
```

### Query by source system
```bash
curl https://<API_URL>/sources/cli-test/objects
```

### Query by bucket and date range
```bash
curl "https://<API_URL>/objects?bucket=<BUCKET_NAME>&start=2025-12-24T00:00:00Z&end=2025-12-25T00:00:00Z"
```

---

## 📁 Project Structure

```
.
├── src
│   ├── ingest
│   │   ├── app.py          # Ingest Lambda (EventBridge + S3)
│   │   └── requirements.txt
│   └── query
│       ├── app.py          # Query Lambda (API)
│       └── requirements.txt
├── template.yaml           # AWS SAM template
├── README.md
└── docs
    └── architecture.gif
```

---

## 🔐 Security & Cost Notes

- DynamoDB uses **PAY_PER_REQUEST**
- IAM permissions follow **least privilege**
- No servers or clusters to manage
- Very low idle cost

Authentication is intentionally omitted and can be added later.

---

## 🔮 Possible Enhancements

### High Priority:

- Add pagination support for large result sets
- Implement error handling with Dead Letter Queues (DLQ)
- Add CloudWatch dashboards for monitoring
- Unit and integration test coverage

### Medium Priority:

- Generate presigned URLs for secure object downloads
- Add API authentication (Cognito/IAM)
- Support object deletion events (catalog cleanup)
- Add more query filters (content type, size range)

### Future Ideas:

- Full-text search integration (OpenSearch)
- Object tagging support
- Multi-region replication
- GraphQL API option

Contributions welcome! Reach out to me directly.

---

## 👤 Author

**Cansu Mericli**
Data Engineer | AWS Enthusiast
cansumericli@gmail.com

Built as a portfolio project to demonstrate:

- Event-driven microservices architecture
- DynamoDB access pattern design
- Serverless best practices
- Infrastructure as Code (IaC)

Built as a **portfolio-grade AWS serverless project** to demonstrate event-driven ingestion, indexing, and API-based access patterns.


## 📝 License
This project is licensed under the MIT License - see LICENSE file for details.

## 🙋 FAQ
Q: Why not use S3 Select or Athena?
A: S3 Select queries individual objects, Athena requires schema definition and is optimized for analytics, not real-time catalog lookups. This solution provides sub-100ms API responses for operational queries.
Q: Does this work with existing S3 buckets?
A: Yes! Just enable EventBridge notifications on your existing bucket and point them to this system. Historical objects require a one-time backfill (not included, but easy to add).
Q: What happens if Lambda fails?
A: EventBridge has built-in retries. Consider adding a Dead Letter Queue (DLQ) for production use to capture failed events.
Q: Can I customize the metadata extracted?
A: Absolutely! Edit src/ingest/app.py to extract custom metadata tags or compute derived fields.