<!-- generated: 2026-09-17 -->
# Project Analysis — Universal Extension v1.0.0

**Extension:** `ue-2-aws-object-storage`
**API Level:** 1.6.0
**Requires Python:** >=3.11
**Owner:** ISS / Stonebranch

---

## Purpose

Enables UAC tasks to interact with Amazon S3 by listing objects stored in a bucket (with formatted ASCII output) or uploading a local file from the Universal Agent host to a specified S3 destination.

---

## Execution Modes / Actions

| Mode | Trigger | Description |
|------|---------|-------------|
| List Objects | `action = "List Objects"` (default) | Paginates S3 bucket objects up to `UE_MAX_OUTPUT_RECORDS` (default 100), prints a rounded ASCII table to STDOUT, emits truncation warning to STDOUT and STDERR when capped, and populates `objects_found` output field. |
| Upload File | `action = "Upload File"` | Validates local file existence on agent host before any AWS call, uploads to specified S3 key, prints confirmation to STDOUT, and populates `uploaded_s3_key` output field. |

---

## Complete Field Table

| # | Name | Label | Type | Field Mapping | Required | Default | Restriction | Notes |
|---|------|-------|------|---------------|----------|---------|-------------|-------|
| 0 | `action` | Action | Choice | Choice Field 1 | No (has default) | `List Objects` | No Restriction | Choices: "List Objects", "Upload File". Drives visibility and requirement of downstream fields. |
| 1 | `aws_credentials` | AWS Credentials | Credential | Credential Field 1 | Yes | — | No Restriction | Runtime User = AWS Access Key ID; Runtime Password = AWS Secret Access Key. |
| 2 | `aws_region` | AWS Region | Text | Text Field 1 | Yes | — | No Restriction | AWS region of the target bucket (e.g. `us-east-1`). Always visible. |
| 3 | `bucket_name` | Bucket Name | Text | Text Field 2 | Yes | — | No Restriction | Name of the target S3 bucket. Always visible. |
| 4 | `local_file_path` | Local File Path | Text | Text Field 3 | When visible | — | No Restriction | Absolute path to local file on agent host to upload (e.g. `/data/reports/file.pdf`). Hidden when action ≠ "Upload File". `noSpaceIfHidden=true`. |
| 5 | `s3_object_key` | S3 Object Key | Text | Text Field 4 | When visible | — | No Restriction | Destination S3 object key (e.g. `reports/file.pdf`). Hidden when action ≠ "Upload File". `noSpaceIfHidden=true`. |
| 6 | `status` | Status | Text | Text Field 10 | — | — | Output Only | Human-readable outcome summary; updated in real-time as action progresses. Always visible. `preserveOutputOnRerun=true`. |
| 7 | `objects_found` | Objects Found | Text | Text Field 11 | — | — | Output Only | Count of S3 objects returned by List Objects. Hidden when action = "Upload File". `preserveOutputOnRerun=true`. |
| 8 | `uploaded_s3_key` | Uploaded S3 Key | Text | Text Field 12 | — | — | Output Only | Destination S3 key where file was stored. Hidden when action = "List Objects". `preserveOutputOnRerun=true`. |

---

## Cross-References

### Always Required
- `aws_credentials`
- `aws_region`
- `bucket_name`

### Conditionally Required (action = "Upload File")
- `local_file_path` — `requireIfVisible=true` + shown only when action = "Upload File"
- `s3_object_key` — `requireIfVisible=true` + shown only when action = "Upload File"

> Both are also validated in Python (`InputFields._validate_local_file_path()` / `_validate_s3_object_key()`), raising `DataValidationError` (exit 20) if missing when action is "Upload File".

### Visibility Dependencies (`showIfField = "Choice Field 1"`)
| Field | Shown When |
|-------|-----------|
| `local_file_path` | action = "Upload File" |
| `s3_object_key` | action = "Upload File" |
| `objects_found` (output) | action = "List Objects" |
| `uploaded_s3_key` (output) | action = "Upload File" |

### Mutually Exclusive Output Fields
- `objects_found` is populated only by **List Objects**.
- `uploaded_s3_key` is populated only by **Upload File**.
- Both are hidden in the UI when the complementary action is selected.

---

## Error Handling

| Scope | Error Class | Exit Code | Trigger |
|-------|-------------|-----------|---------|
| Input validation | `DataValidationError` | 20 | Invalid action value, empty `aws_region`, empty `bucket_name`, or missing `local_file_path`/`s3_object_key` when action = "Upload File". Raised in `InputFields.__post_init__()`. |
| Upload pre-flight | `AWSValidationError` | 20 | `local_file_path` does not exist on the agent host filesystem. Checked before any boto3 call. |
| AWS authentication | `AWSAuthenticationError` | 1 | boto3 `ClientError` codes: `InvalidClientTokenId`, `SignatureDoesNotMatch`, `AuthFailure` — invalid Access Key ID or Secret Access Key. |
| AWS authorization | `AWSAuthorizationError` | 1 | boto3 `ClientError` code: `AccessDenied` — credentials valid but IAM policy denies the requested operation on the bucket. |
| AWS configuration | `AWSConfigurationError` | 1 | boto3 `ClientError` code: `NoSuchBucket` — bucket does not exist or is in a different region than `aws_region`. |
| AWS general | `AWSUnexpectedError` | 1 | Any other boto3 `ClientError`, network error, or OS error not mapped to a more specific class. |
| Cancellation | `ExecutionError` | 1 | `extension_manager.is_cancelled()` checked at two points per action (before S3 client init and before the core operation); raises "Operation cancelled by user". |
| System catch-all | `UnexpectedSystemError` | 1 | Any unhandled Python exception in `extension_start()`; wraps the exception message for UAC status output. |
