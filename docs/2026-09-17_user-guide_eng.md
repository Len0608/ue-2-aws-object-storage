> **Version:** 1.0.0 | **Date:** 2026-09-17

# AWS Object Storage — User Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Task Actions](#task-actions)
   - [List Objects](#list-objects)
   - [Upload File](#upload-file)
4. [Task Configuration](#task-configuration)
   - [Authentication](#authentication)
   - [General](#general)
   - [Upload File Fields](#upload-file-fields)
   - [Output Fields](#output-fields)
5. [Example Walkthrough](#example-walkthrough)
   - [Scenario 1 — List objects in a reporting bucket](#scenario-1--list-objects-in-a-reporting-bucket)
   - [Scenario 2 — Upload a daily report to S3](#scenario-2--upload-a-daily-report-to-s3)
6. [Troubleshooting](#troubleshooting)
7. [Field Reference](#field-reference)

---

## Overview

The **AWS Object Storage** Universal Extension enables Stonebranch UAC tasks to interact with Amazon S3 directly from a scheduled workflow. It provides two operations:

- **List Objects** — retrieve and display objects stored in an S3 bucket, including key, size, and last-modified timestamp.
- **Upload File** — upload a local file from the Universal Agent host to a specified S3 bucket and object key.

Authentication is handled exclusively through a UAC Credential object that stores an AWS IAM Access Key ID and Secret Access Key. All dependencies (boto3, tabulate) are bundled with the extension — nothing needs to be installed on the Universal Agent host.

---

## Prerequisites

- A Stonebranch UAC instance with a **Universal Agent** running on Linux (x86_64).
- An **AWS IAM user** with the following permissions on the target S3 bucket:
  - `s3:ListObjectsV2` — required for the **List Objects** action.
  - `s3:PutObject` — required for the **Upload File** action.
- The IAM user's **Access Key ID** and **Secret Access Key** available for credential creation.
- A **UAC Credential** object configured with:
  - **Runtime User** = AWS Access Key ID
  - **Runtime Password** = AWS Secret Access Key
- The target **S3 bucket** must exist in the specified AWS region before running the task.
- For **Upload File**: the file to upload must exist on the filesystem of the Universal Agent host at the time the task runs.

---

## Task Actions

### List Objects

Lists all objects stored in the specified S3 bucket and prints a formatted table to the task output. Output includes the object key, human-readable file size, and last-modified timestamp (UTC).

**When to use:** Use this action to audit bucket contents, verify that expected files exist, or retrieve metadata for downstream workflow decisions.

**Execution flow:**

1. The extension reads the `UE_MAX_OUTPUT_RECORDS` environment variable to determine the output cap (default: 100).
2. An S3 client is initialized using the provided IAM credentials and region.
3. The bucket is paginated using `ListObjectsV2`. Collection stops when the cap is reached or no more objects remain.
4. A formatted ASCII table is printed to STDOUT with columns **Object Key**, **Size**, and **Last Modified**.
5. If the result is capped and more objects exist, a truncation notice is printed to STDOUT and a warning is written to STDERR.
6. Output fields `Status` and `Objects Found` are populated.

**Expected output example:**

```
╭──────────────────────────────────────┬──────────┬──────────────────────────╮
│ Object Key                           │ Size     │ Last Modified            │
├──────────────────────────────────────┼──────────┼──────────────────────────┤
│ reports/monthly-2024-01.pdf          │ 1.2 MB   │ 2024-01-15T10:23:00Z     │
│ data/export-2024-02.csv              │ 45.6 KB  │ 2024-02-20T08:15:00Z     │
╰──────────────────────────────────────┴──────────┴──────────────────────────╯
```

**Completion behavior:** The task exits with code `0` on success. The `Status` output field contains a summary such as `Success: Found 42 objects in bucket 'my-demo-bucket'`.

---

### Upload File

Uploads a local file from the Universal Agent host to the specified S3 bucket at the given object key. The extension validates that the file exists before making any AWS API call.

**When to use:** Use this action to archive generated reports, export data files, or push any file produced by a prior workflow step to long-term S3 storage.

**Execution flow:**

1. The extension checks that the file at **Local File Path** exists on the agent host. If not, the task fails immediately with exit code `20` (no AWS call is made).
2. An S3 client is initialized using the provided IAM credentials and region.
3. The file is uploaded using boto3's `upload_file` method, which handles multipart upload transparently for large files.
4. A confirmation line is printed to STDOUT: `Uploaded <path> to s3://<bucket>/<key>`.
5. Output fields `Status` and `Uploaded S3 Key` are populated.

**Re-run behavior:** Re-running an Upload File task re-uploads the file, overwriting any existing object at the same S3 object key. This is standard S3 behavior.

**Completion behavior:** The task exits with code `0` on success. The `Status` output field contains a summary such as `Success: File uploaded to s3://my-demo-bucket/reports/monthly-2024-01.pdf`.

---

## Task Configuration

### Authentication

| Field | Description |
|---|---|
| **AWS Credentials** | UAC Credential object providing IAM authentication. Set **Runtime User** to the AWS Access Key ID and **Runtime Password** to the AWS Secret Access Key. |

### General

| Field | Description |
|---|---|
| **Action** | The S3 operation to perform. Select **List Objects** or **Upload File**. Selecting **Upload File** reveals the upload-specific fields below. |
| **AWS Region** | The AWS region where the target S3 bucket is located (e.g. `us-east-1`, `eu-west-1`). |
| **Bucket Name** | The name of the target S3 bucket (e.g. `my-demo-bucket`). The bucket must already exist. |

### Upload File Fields

These fields are visible only when **Action** is set to **Upload File**.

| Field | Description |
|---|---|
| **Local File Path** | Absolute path to the file on the Universal Agent host to upload (e.g. `/data/reports/monthly-2024-01.pdf`). The file must exist at task launch time. |
| **S3 Object Key** | Destination key within the S3 bucket (e.g. `reports/monthly-2024-01.pdf`). This is the full path under which the object will be stored in S3. |

### Output Fields

These fields are read-only and populated by the extension after task execution.

| Field | Description | Visible When |
|---|---|---|
| **Status** | Human-readable summary of the action outcome (success or error message). | Always |
| **Objects Found** | Count of S3 objects returned by the List Objects action. | List Objects only |
| **Uploaded S3 Key** | Destination S3 object key where the uploaded file was stored. | Upload File only |

---

## Example Walkthrough

### Scenario 1 — List objects in a reporting bucket

**Goal:** Retrieve the list of objects stored in an S3 bucket used for monthly reporting files and display them in the task output.

**Prerequisites:**
- A UAC Credential exists with an AWS Access Key ID (Runtime User) and Secret Access Key (Runtime Password).
- The IAM user has `s3:ListObjectsV2` permission on the `finance-reports` bucket.
- The S3 bucket `finance-reports` exists in `us-east-1`.
- A Universal Agent is running and reachable by UAC.

**Configuration:**

| Field | Value | Notes |
|---|---|---|
| Action | List Objects | |
| AWS Credentials | `cred-aws-finance` | Select the UAC credential holding the IAM keys |
| AWS Region | `us-east-1` | Must match the bucket's region |
| Bucket Name | `finance-reports` | |

**What happens:**

- The extension connects to S3 in `us-east-1` using the provided IAM credentials.
- All objects in `finance-reports` (up to 100 by default) are retrieved and printed as an ASCII table showing key, size, and last-modified date.
- The `Status` output field shows `Success: Found N objects in bucket 'finance-reports'`.
- The `Objects Found` output field shows the count of returned objects.
- If more than 100 objects exist, a truncation notice is shown and `Objects Found` reflects the capped count.

---

### Scenario 2 — Upload a daily report to S3

**Goal:** Archive a CSV report generated by a prior workflow step on the agent host by uploading it to a designated S3 bucket.

**Prerequisites:**
- A UAC Credential exists with an AWS Access Key ID (Runtime User) and Secret Access Key (Runtime Password).
- The IAM user has `s3:PutObject` permission on the `ops-archive` bucket.
- The S3 bucket `ops-archive` exists in `eu-west-1`.
- The file `/tmp/reports/daily-ops-2026-09-17.csv` exists on the Universal Agent host at task launch time.

**Configuration:**

| Field | Value | Notes |
|---|---|---|
| Action | Upload File | |
| AWS Credentials | `cred-aws-ops` | Select the UAC credential holding the IAM keys |
| AWS Region | `eu-west-1` | Must match the bucket's region |
| Bucket Name | `ops-archive` | |
| Local File Path | `/tmp/reports/daily-ops-2026-09-17.csv` | Absolute path on the agent host |
| S3 Object Key | `reports/2026/09/daily-ops-2026-09-17.csv` | Destination path within the bucket |

**What happens:**

- The extension first verifies that `/tmp/reports/daily-ops-2026-09-17.csv` exists on the agent host. If not, the task fails immediately with exit code 20.
- The file is uploaded to `s3://ops-archive/reports/2026/09/daily-ops-2026-09-17.csv` via the S3 API.
- A confirmation line is printed to STDOUT: `Uploaded /tmp/reports/daily-ops-2026-09-17.csv to s3://ops-archive/reports/2026/09/daily-ops-2026-09-17.csv`.
- The `Status` output field shows `Success: File uploaded to s3://ops-archive/reports/2026/09/daily-ops-2026-09-17.csv`.
- The `Uploaded S3 Key` output field shows `reports/2026/09/daily-ops-2026-09-17.csv`.

---

## Troubleshooting

### Authentication failure — invalid credentials

**Symptom:** Task fails with status `Authentication Error: Invalid AWS Access Key ID or Secret Access Key`.

**Possible cause:** The UAC Credential has an incorrect Access Key ID (Runtime User) or Secret Access Key (Runtime Password), or the IAM access keys have been rotated or deactivated.

**Resolution:**
1. Verify the Access Key ID and Secret Access Key in the AWS IAM console.
2. Update the UAC Credential object (`Runtime User` = Access Key ID, `Runtime Password` = Secret Access Key).
3. Confirm the IAM user is active and the keys are not expired.

---

### Permission denied — IAM authorization error

**Symptom:** Task fails with status `Authorization Error: Access denied — check IAM permissions for bucket '<bucket>'`.

**Possible cause:** The IAM user associated with the credentials does not have the required S3 permission (`s3:ListObjectsV2` for List Objects, `s3:PutObject` for Upload File) on the target bucket.

**Resolution:**
1. Open the AWS IAM console and locate the policy attached to the IAM user.
2. Add or confirm the following permissions on the target bucket ARN (`arn:aws:s3:::<bucket-name>/*`):
   - `s3:ListObjectsV2` for the List Objects action.
   - `s3:PutObject` for the Upload File action.
3. If the bucket has a bucket policy, verify it does not explicitly deny access.

---

### Bucket not found — configuration error

**Symptom:** Task fails with status `Configuration Error: Bucket '<bucket>' does not exist or is in a different region`.

**Possible cause:** The bucket name is misspelled, the bucket has not been created yet, or the **AWS Region** field does not match the actual region where the bucket is hosted.

**Resolution:**
1. Verify the bucket name in the **Bucket Name** field exactly matches the S3 bucket name (case-sensitive).
2. Confirm the bucket exists in the AWS S3 console.
3. Ensure the **AWS Region** field matches the bucket's region (e.g. `us-east-1` not `us-east1`).

---

### Local file not found — validation error (exit code 20)

**Symptom:** Task fails with status `Validation Error: Local file '<path>' not found on the agent host` and exits with code 20.

**Possible cause:** The path in **Local File Path** does not exist on the Universal Agent host at the time the task runs, or it contains a typo.

**Resolution:**
1. Log in to the agent host and confirm the file exists at the specified path.
2. Verify the path is absolute (starts with `/`).
3. Check file permissions — the Universal Agent process must be able to read the file.
4. If the file is generated by a prior step, confirm that step completed successfully before the upload task runs.

---

### Output truncated — bucket contains more objects than displayed

**Symptom:** A notice appears in the task output: `Note: Results are limited to 100 records. The bucket may contain additional objects.`

**Possible cause:** The bucket contains more objects than the `UE_MAX_OUTPUT_RECORDS` cap (default: 100). The `Objects Found` field reflects the capped count, not the total bucket size.

**Resolution:**
- If you need to see more objects, increase `UE_MAX_OUTPUT_RECORDS` by setting it as an environment variable on the agent or task. For example, set `UE_MAX_OUTPUT_RECORDS=500` to retrieve up to 500 objects.
- This is informational only — the task still exits with code 0 and is considered successful.

---

### Connection timeout or network error

**Symptom:** Task fails with `Unexpected Error: ...` and the message references a connection or socket timeout.

**Possible cause:** The Universal Agent host cannot reach the AWS S3 endpoint (`https://s3.<region>.amazonaws.com`) due to network restrictions, a firewall rule, or a proxy configuration.

**Resolution:**
1. From the agent host, verify outbound HTTPS (port 443) access to `s3.<region>.amazonaws.com`.
2. If a proxy is required, confirm it is configured in the agent's environment.
3. Check that the **AWS Region** value is a valid AWS region identifier (e.g. `us-east-1`).

---

## Field Reference

| Field Name | Label | Type | Required | Description | Allowed Values / Example |
|---|---|---|---|---|---|
| `action` | Action | Choice | Yes | The S3 operation to perform. Defaults to **List Objects**. | `List Objects`, `Upload File` |
| `aws_credentials` | AWS Credentials | Credential | Yes | UAC Credential supplying IAM authentication. Runtime User = Access Key ID; Runtime Password = Secret Access Key. | Any valid UAC Credential |
| `aws_region` | AWS Region | Text | Yes | AWS region where the target S3 bucket is located. | e.g. `us-east-1`, `eu-west-1` |
| `bucket_name` | Bucket Name | Text | Yes | Name of the target S3 bucket. | e.g. `my-demo-bucket` |
| `local_file_path` | Local File Path | Text | When Action = Upload File | Absolute path to the local file on the agent host to upload. | e.g. `/data/reports/monthly-2024-01.pdf` |
| `s3_object_key` | S3 Object Key | Text | When Action = Upload File | Destination S3 object key (path within the bucket) where the file will be stored. | e.g. `reports/monthly-2024-01.pdf` |
| `status` | Status | Text (Output Only) | — | Human-readable summary of the action outcome. Set by the extension on success and failure. | Populated automatically |
| `objects_found` | Objects Found | Text (Output Only) | — | Count of S3 objects returned. Visible only when Action = List Objects. | Populated automatically |
| `uploaded_s3_key` | Uploaded S3 Key | Text (Output Only) | — | Destination S3 object key where the uploaded file was stored. Visible only when Action = Upload File. | Populated automatically |
