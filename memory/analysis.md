# AWS Object Storage - Implementation Analysis

**Extension Name:** AWS Object Storage (ue-2-aws-object-storage)
**Universal Template Name:** Ue 2 Aws Object Storage
**Target Platform:** Linux

---

## Extension Overview

The AWS Object Storage Universal Extension enables UAC task operators to interact with Amazon S3 directly from the Stonebranch platform. It provides two operations: listing objects within a specified S3 bucket (with a formatted ASCII table output and a configurable record cap), and uploading a local file from the Universal Agent host to a specified S3 bucket at a given object key. Authentication is exclusively via static IAM credentials (Access Key ID and Secret Access Key) supplied through a UAC credential object. The scope is intentionally MVP/demo — simple, with no advanced features.

---

# Template Fields

## 1. Input Fields

**action**
- **Type**: Choice Field (Single-select)
- **Visible When**: always
- **Required When**: always
- **Options**:
  - List Objects - List objects stored in the S3 bucket with key, size, and last-modified details
  - Upload File - Upload a local file from the agent host to the S3 bucket
- **Default Value**: List Objects
- **Validation**:
  - Must be one of the options
- **Purpose**: Determines which S3 operation to execute. Selecting Upload File reveals upload-specific input fields; those fields are hidden when List Objects is selected.

**aws_credentials**
- **Type**: Credential Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must reference a valid UAC Credential. Runtime User must contain the AWS Access Key ID; Runtime Password must contain the AWS Secret Access Key.
- **Purpose**: Supplies AWS IAM credentials for authenticating to the S3 API. Hint text: "Runtime User: AWS Access Key ID | Runtime Password: AWS Secret Access Key."

**aws_region**
- **Type**: Text Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must not be empty
- **Purpose**: The AWS region where the target S3 bucket is located
- **Example**: `us-east-1`

**bucket_name**
- **Type**: Text Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must not be empty
- **Purpose**: The name of the target S3 bucket on which the action is performed
- **Example**: `my-demo-bucket`

**local_file_path**
- **Type**: Text Field
- **Visible When**: `action` value is equal to "Upload File". It is required when it's visible.
- **Required When**: `action` value is equal to "Upload File"
- **Validation**:
  - Must not be empty
  - File existence on the agent host is validated at runtime before any AWS API call is made
- **Purpose**: The absolute path to the local file on the Universal Agent host that will be uploaded to S3
- **Example**: `/data/reports/monthly-2024-01.pdf`

**s3_object_key**
- **Type**: Text Field
- **Visible When**: `action` value is equal to "Upload File". It is required when it's visible.
- **Required When**: `action` value is equal to "Upload File"
- **Validation**:
  - Must not be empty
- **Purpose**: The destination S3 object key (path within the bucket) where the uploaded file will be stored
- **Example**: `reports/monthly-2024-01.pdf`

---

## 2. Output Fields

**status**
- **Type**: Text Output
- **Purpose**: Human-readable summary of the action outcome. Marked as the extensionStatus field. Populated on both success and failure.
- **Examples**: "Success: Found 42 objects in bucket 'my-demo-bucket'", "Success: File uploaded to s3://my-demo-bucket/reports/monthly-2024-01.pdf"

**objects_found**
- **Type**: Text Output
- **Visible When**: `action` is "List Objects"
- **Purpose**: The count of S3 objects returned by the List Objects action (up to the UE_MAX_OUTPUT_RECORDS cap)
- **Examples**: "42", "100"

**uploaded_s3_key**
- **Type**: Text Output
- **Visible When**: `action` is "Upload File"
- **Purpose**: The destination S3 object key where the file was successfully stored
- **Examples**: "reports/monthly-2024-01.pdf", "data/archive/2024/report.csv"

---

## 3. Field Ordering

The task form uses a **2-column grid layout**. Fields can be displayed in two ways:

- **Full-width fields**: Span both columns (typically for dropdowns, credentials, or primary selections)
- **Half-width fields**: Occupy one column, allowing two fields side-by-side (typically for related pairs)

**Layout Rules:**
- Credential fields ALWAYS span full-width (both columns)
- Group related fields side-by-side when logical (e.g., country/city, latitude/longitude)
- Primary selection fields typically span full-width for prominence

**Field Order (Visual Layout):**

```
┌─────────────────────────────────────────┐
│                 action                  │  ← Full-width
├─────────────────────────────────────────┤
│             aws_credentials             │  ← Full-width (credential)
├─────────────────────────────────────────┤
│   aws_region      │    bucket_name      │  ← Half-width pair
├───────────────────┼─────────────────────┤
│           local_file_path               │  ← Full-width (Upload File only)
├─────────────────────────────────────────┤
│             s3_object_key               │  ← Full-width (Upload File only)
├─────────────────────────────────────────┤
│                 status                  │  ← Full-width (Output Only)
├─────────────────────────────────────────┤
│             objects_found               │  ← Full-width (Output Only, List Objects only)
├─────────────────────────────────────────┤
│            uploaded_s3_key              │  ← Full-width (Output Only, Upload File only)
└─────────────────────────────────────────┘
```

---

# Actions

## Action 1: List Objects

**Description**: Lists objects stored in the specified AWS S3 bucket. Returns object key, human-readable size, and last-modified timestamp per object, formatted as an ASCII table on STDOUT. Output is capped at `UE_MAX_OUTPUT_RECORDS` (default: 100) records. When the cap is reached and more objects exist, a truncation warning is emitted on STDOUT and STDERR, and the `truncated` flag in Extension Output is set to `true`.

### Input Requirements

- **action** (value: "List Objects")
- **aws_credentials**
- **aws_region**
- **bucket_name**

### Execution Flow

**Step 1: Resolve output record cap**
- Read `UE_MAX_OUTPUT_RECORDS` from the process environment. If absent or not a valid positive integer, default to `100`. Store as integer `cap`.

**Step 2: Initialize S3 client**
- Extract `access_key_id` from `aws_credentials["user"]`
- Extract `secret_access_key` from `aws_credentials["password"]`
- Create a boto3 S3 client explicitly configured with `aws_access_key_id`, `aws_secret_access_key`, and `region_name`. Do not fall back to any implicit credential chain.

**Step 3: Paginate and collect objects up to cap**
- Initialize `collected = []` and `truncated = False`
- Use manual pagination with `ContinuationToken`:
  - On each iteration, call `list_objects_v2` with `Bucket = bucket_name` and `MaxKeys = min(cap - len(collected), 1000)`
  - Extend `collected` with all objects from the response's `Contents` list (if present; an empty bucket returns no `Contents` key)
  - If `len(collected) >= cap` AND the response's `IsTruncated` is `True`: set `truncated = True` and stop iteration
  - If the response's `IsTruncated` is `False`: stop iteration (`truncated` remains `False`)
  - Otherwise: extract `NextContinuationToken` from response and repeat

**Step 4: Format and print ASCII table to STDOUT**
- For each object in `collected`, build a display row:
  - `key`: object's `Key` string value
  - `size`: convert object's `Size` (bytes integer) to human-readable string using the Output Formatter utility
  - `last_modified`: format object's `LastModified` (timezone-aware datetime) to ISO 8601 UTC string using the Output Formatter utility
- Generate ASCII table with headers `["Object Key", "Size", "Last Modified"]` and `tablefmt="rounded_outline"` using tabulate
- Print the table to STDOUT

**Step 5: Emit truncation warning (if applicable)**
- If `truncated = True`:
  - Print to STDOUT: `"Note: Results are limited to {cap} records. The bucket may contain additional objects."`
  - Emit STDERR warning: `"WARNING: Output truncated to {cap} records (UE_MAX_OUTPUT_RECORDS={cap}). Additional objects exist in the bucket."`

**Step 6: Populate output-only fields**
- `output_data.status` = `"Success: Found {len(collected)} objects in bucket '{bucket_name}'"`
- `output_data.objects_found` = `str(len(collected))`

**Step 7: Build Extension Output result**
- Construct the `objects` array: for each collected object, include `{"key": key, "size_bytes": size_int, "last_modified": iso_string}`
- Emit result with `bucket`, `object_count`, `truncated`, and `objects` fields (see Output Examples)

**Step 8: Close S3 client and return exit code 0**

### Output Examples

**STDOUT**:
```
╭──────────────────────────────────────┬──────────┬──────────────────────────╮
│ Object Key                           │ Size     │ Last Modified            │
├──────────────────────────────────────┼──────────┼──────────────────────────┤
│ reports/monthly-2024-01.pdf          │ 1.2 MB   │ 2024-01-15T10:23:00Z     │
│ data/export-2024-02.csv              │ 45.6 KB  │ 2024-02-20T08:15:00Z     │
╰──────────────────────────────────────┴──────────┴──────────────────────────╯
```
When truncated, an additional line follows the table:
```
Note: Results are limited to 100 records. The bucket may contain additional objects.
```

**Extension Output result object (JSON)**:

The Extension Output also includes `exit_code`, `status_description`, and `invocation` elements that are added automatically during implementation time. The `result` object for this action is:

```json
{
  "result": {
    "bucket": "my-demo-bucket",
    "object_count": 42,
    "truncated": false,
    "objects": [
      { "key": "reports/monthly-2024-01.pdf", "size_bytes": 1258291, "last_modified": "2024-01-15T10:23:00Z" },
      { "key": "data/export-2024-02.csv", "size_bytes": 46694, "last_modified": "2024-02-20T08:15:00Z" }
    ]
  }
}
```

### Success Criteria

1. boto3 S3 API call completes without error
2. Object list (up to cap) is formatted and printed to STDOUT as an ASCII table with columns Object Key, Size, Last Modified
3. Truncation warning is printed to STDOUT and STDERR when the result set is capped and more objects exist
4. `status` output-only field is populated with the success summary
5. `objects_found` output-only field is populated with the count of returned objects
6. Extension Output JSON is emitted with a `result` object containing `bucket`, `object_count`, `truncated`, and `objects`
7. Return code is 0

---

## Action 2: Upload File

**Description**: Uploads a local file from the Universal Agent host to the specified AWS S3 bucket at the specified S3 object key. Validates local file existence before any AWS API call. On success, populates the `Uploaded S3 Key` output field and prints a confirmation to STDOUT.

### Input Requirements

- **action** (value: "Upload File")
- **aws_credentials**
- **aws_region**
- **bucket_name**
- **local_file_path**
- **s3_object_key**

### Execution Flow

**Step 1: Validate local file existence**
- Check whether the file at `local_file_path` exists on the agent filesystem
- If the file does not exist: raise `AWSValidationError` immediately with message `"Local file '<local_file_path>' not found on the agent host"` (exit code 20). No AWS API call is made.

**Step 2: Initialize S3 client**
- Extract `access_key_id` from `aws_credentials["user"]`
- Extract `secret_access_key` from `aws_credentials["password"]`
- Create a boto3 S3 client explicitly configured with `aws_access_key_id`, `aws_secret_access_key`, and `region_name`. Do not fall back to any implicit credential chain.

**Step 3: Upload file to S3**
- Call `upload_file(local_file_path, bucket_name, s3_object_key)` on the S3 client
- boto3's `upload_file` handles multipart upload automatically for large files; no additional logic is needed

**Step 4: Print confirmation to STDOUT**
- Print: `"Uploaded {local_file_path} to s3://{bucket_name}/{s3_object_key}"`

**Step 5: Populate output-only fields**
- `output_data.status` = `"Success: File uploaded to s3://{bucket_name}/{s3_object_key}"`
- `output_data.uploaded_s3_key` = `s3_object_key`

**Step 6: Build Extension Output result**
- Emit result with `bucket`, `key`, and `s3_uri` fields (see Output Examples)

**Step 7: Close S3 client and return exit code 0**

### Output Examples

**STDOUT**:
```
Uploaded /data/reports/monthly-2024-01.pdf to s3://my-demo-bucket/reports/monthly-2024-01.pdf
```

**Extension Output result object (JSON)**:

The Extension Output also includes `exit_code`, `status_description`, and `invocation` elements that are added automatically during implementation time. The `result` object for this action is:

```json
{
  "result": {
    "bucket": "my-demo-bucket",
    "key": "reports/monthly-2024-01.pdf",
    "s3_uri": "s3://my-demo-bucket/reports/monthly-2024-01.pdf"
  }
}
```

### Success Criteria

1. Local file exists and is readable on the agent host
2. boto3 S3 upload completes without error
3. `status` output-only field is populated with the success summary
4. `uploaded_s3_key` output-only field is populated with the destination S3 object key
5. Extension Output JSON is emitted with a `result` object containing `bucket`, `key`, and `s3_uri`
6. Return code is 0

---

# Progress Reporting

Progress Reporting (percentage of completion report) is not required. STDOUT displays the result upon action completion.

---

# Dynamic Choice Field Population

No Dynamic choice fields should be implemented.

---

# Cancellation Behavior

Default cancellation behavior (TERM signal) is used. No custom cancellation logic is required.

---

# Re-Run Behavior

Re-runs are treated as initial executions. No special re-run logic is required. Re-running a List Objects task performs a fresh listing. Re-running an Upload File task re-uploads the file to the same S3 object key, overwriting any existing object at that key — this is standard S3 behavior and is acceptable for MVP scope.

---

# Dynamic Commands

No Dynamic commands should be implemented.

---

# Utility Modules

## Required Utility Modules

### 1. S3 Client Utility

**Purpose:** Manages the boto3 S3 client lifecycle and encapsulates all AWS S3 API interactions, including client initialization, S3 operations, and error classification.

**Required Capabilities:**
- Initialize an S3 client using only explicit credentials (Access Key ID, Secret Access Key) and region. Must not fall back to implicit credential chains (environment variables, `~/.aws/credentials`, IAM instance profiles).
- List objects in a bucket with manual pagination support: accept a cap parameter, iterate through pages collecting objects, stop when the cap is reached or no more pages exist, and return both the collected object list and a boolean `truncated` flag.
- Upload a local file to a specified bucket at a specified object key using boto3's `upload_file` method, which transparently handles multipart upload for large files.
- Classify boto3 `ClientError` exceptions by their error code into the extension's custom exception hierarchy (see Exception Mapping Strategy below).
- Properly close or release the S3 client after each operation, whether on success or failure.

**Used By:** List Objects action, Upload File action

---

### 2. Output Formatter Utility

**Purpose:** Provides formatting functions for transforming raw S3 object data into human-readable strings suitable for STDOUT table display.

**Required Capabilities:**

**Size Formatting:**
- Convert a raw byte count (integer) to a human-readable size string with the appropriate unit suffix
- Scaling rules: < 1 024 → `"{N} B"`, < 1 048 576 → `"{N:.1f} KB"`, < 1 073 741 824 → `"{N:.1f} MB"`, < 1 099 511 627 776 → `"{N:.1f} GB"`, otherwise → `"{N:.1f} TB"`
- Examples: 512 → "512 B", 46694 → "45.6 KB", 1258291 → "1.2 MB"

**Timestamp Formatting:**
- Convert a timezone-aware datetime object (as returned by boto3 for `LastModified`) to an ISO 8601 UTC string in the format `"YYYY-MM-DDTHH:MM:SSZ"`
- Normalize to UTC regardless of the datetime object's original timezone

**ASCII Table Generation:**
- Accept a list of dicts with keys `key` (str), `size` (human-readable str), and `last_modified` (ISO 8601 str)
- Generate a formatted ASCII table using tabulate with headers `["Object Key", "Size", "Last Modified"]` and `tablefmt="rounded_outline"`
- Return the formatted table string for printing to STDOUT

**Used By:** List Objects action

---

## Exception Mapping Strategy

**boto3 ClientError Code Mapping:**
- `InvalidClientTokenId` → `AWSAuthenticationError` (exit code 1, non-transient — invalid Access Key ID)
- `SignatureDoesNotMatch` → `AWSAuthenticationError` (exit code 1, non-transient — invalid Secret Access Key)
- `AuthFailure` → `AWSAuthenticationError` (exit code 1, non-transient — general authentication failure)
- `AccessDenied` → `AWSAuthorizationError` (exit code 1, non-transient — IAM permission denied on bucket)
- `NoSuchBucket` → `AWSConfigurationError` (exit code 1, non-transient — bucket does not exist or is in a different region)
- Any other ClientError code → `AWSUnexpectedError` (exit code 1, may be transient)

**Pre-flight Validation Errors:**
- Local file path does not exist on the agent filesystem → `AWSValidationError` (exit code 20, non-transient, user input error)

**All Other Exceptions:**
- Any non-ClientError exception (network failures, OS errors, boto3 internal errors) → `AWSUnexpectedError` (exit code 1, may be transient)

**Status Descriptions by Exception Type:**

| Exception Class | Status Description |
|---|---|
| AWSAuthenticationError | `"Authentication Error: Invalid AWS Access Key ID or Secret Access Key"` |
| AWSAuthorizationError | `"Authorization Error: Access denied — check IAM permissions for bucket '<bucket>'"` |
| AWSConfigurationError | `"Configuration Error: Bucket '<bucket>' does not exist or is in a different region"` |
| AWSValidationError | `"Validation Error: Local file '<path>' not found on the agent host"` |
| AWSUnexpectedError | `"Unexpected Error: <original exception message>"` |

**Exit Code Guide:**
- Exit code 0: Successful execution
- Exit code 1: Failed execution (authentication, authorization, configuration, or unexpected error)
- Exit code 20: Validation error (user input error — local file not found)

---

# Dependencies

## 1. External API Dependencies

**1. AWS S3 (Amazon Simple Storage Service)**
- **Endpoint**: `https://s3.<region>.amazonaws.com/` (region-specific; resolved automatically by boto3 from the `aws_region` field value)
- **Purpose**: Provides object listing and file upload operations on S3 buckets
- **Protocol**: HTTPS
- **Method**: GET (ListObjectsV2), PUT (PutObject / multipart upload)
- **Authentication**: AWS Signature Version 4, using Access Key ID and Secret Access Key (handled internally by boto3)
- **Response Format**: XML responses parsed by boto3 and presented as Python dictionaries
- **Data Retrieved/Sent**: Object keys, sizes (bytes), last-modified timestamps for listing; binary file content and object key for upload

**General API Requirements:**
- IAM user or role associated with the credentials must have `s3:ListObjectsV2` permission on the target bucket for the List Objects action
- IAM user or role must have `s3:PutObject` permission on the target bucket for the Upload File action
- No AWS console access or additional account configuration is required beyond the IAM permissions above

---

## 2. Python version dependency

Python >= 3.11

---

## 3. Target Platform

Linux (x86_64). C extension modules with a confirmed `manylinux_2_17_x86_64` wheel are viable in addition to pure-Python modules. All runtime dependencies for this extension (`boto3`, `tabulate`, and their transitive dependencies) are pure-Python and carry no binary compatibility concerns.

---

## 4. Python Library Dependencies

**1. boto3**
- **Purpose**: Official AWS SDK for Python; provides the S3 client used for all API interactions
- **Version**: ==1.43.96
- **Installation**: `pip install boto3==1.43.96`
- **Usage**: S3 client initialization, `list_objects_v2` pagination, `upload_file` method, `ClientError` exception handling
- **Features Used**: `boto3.client('s3')`, `client.list_objects_v2()`, `client.upload_file()`, `botocore.exceptions.ClientError`

**2. tabulate**
- **Purpose**: Formats list-of-rows data as a styled ASCII table for human-readable STDOUT output
- **Version**: ==0.10.0
- **Installation**: `pip install tabulate==0.10.0`
- **Usage**: List Objects action STDOUT table generation
- **Features Used**: `tabulate()` function with `tablefmt="rounded_outline"`

---

## 5. Python Standard Library Dependencies

**1. os**
- **Purpose**: Filesystem operations for local file existence validation
- **Version**: Built-in (Python 3.11+)
- **Installation**: No installation required (standard library)
- **Usage**: Upload File pre-flight validation before any AWS call
- **Features Used**: `os.path.exists()`

**2. json**
- **Purpose**: Extension Output JSON serialization
- **Version**: Built-in (Python 3.11+)
- **Installation**: No installation required (standard library)
- **Usage**: Serialize result and error dictionaries to JSON for Extension Output
- **Features Used**: `json.dumps()`

---

## 6. CLI Tool Dependencies

No Dependencies.

---

## 7. Environment Variables

**UE_MAX_OUTPUT_RECORDS** (integer, optional):
- **Purpose**: Controls the maximum number of S3 objects returned and displayed during the List Objects action. Acts as a safety cap to prevent large bucket listings from bloating UAC database storage or exceeding agent output limits.
- **Default**: 100
- **Usage**: Read at the start of List Objects execution. Applied as the pagination cap. Influences the `truncated` flag and truncation warning output.
- **Examples**: `100`, `500`, `1000`
