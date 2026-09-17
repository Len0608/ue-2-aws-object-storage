# Universal Extension Requirements (Refined)

**Extension Name:** AWS Object Storage
**Original Generated:** 2026-09-17 17:42:24
**Refined:** 2026-09-17
**Agent_id:** 2
**Requirements Completeness:** Moderate Detail
**Target Platform:** Linux

---

# Table of Contents

1. [Overview](#overview)
2. [Actions](#actions)
   - 2.1 [Action 1 — List Objects](#action-1-list-objects)
   - 2.2 [Action 2 — Upload File](#action-2-upload-file)
3. [Input Requirements](#input-requirements)
   - 3.1 [Action Selection](#action-selection)
   - 3.2 [Connection Parameters](#connection-parameters)
   - 3.3 [Upload-Specific Parameters](#upload-specific-parameters)
4. [Output Requirements](#output-requirements)
   - 4.1 [On Success](#on-success)
   - 4.2 [On Error](#on-error)
5. [Authentication Requirements](#authentication-requirements)
6. [Environment Variables](#environment-variables)
7. [Operational Behavior](#operational-behavior)
8. [Implementation Notes](#implementation-notes)
   - 8.1 [Python Compatibility](#python-compatibility)
   - 8.2 [Target Platform](#target-platform)
   - 8.3 [Third-Party Services and Tools](#third-party-services-and-tools)
   - 8.4 [Error Handling](#error-handling)
   - 8.5 [Resource Cleanup](#resource-cleanup)
9. [Requirements Summary](#requirements-summary)
10. [Document Change History](#document-change-history)
11. [References](#references)

---

# Overview

This document defines the functional requirements for the **AWS Object Storage** Universal Extension for Stonebranch Universal Automation Center (UAC).

**Integration Purpose:** The extension provides a simple, demo-quality AWS S3 integration that allows UAC task operators to list objects within an S3 bucket and upload local files from a Universal Agent host to an S3 bucket. The goal is to demonstrate that AWS S3 operations can be driven from the Stonebranch platform. The scope is intentionally MVP/demo — the implementation must remain simple and avoid unnecessary advanced features.

---

# Actions

## Action 1 — List Objects

**Functional Requirements:**

1. The action must list objects stored in the specified AWS S3 bucket.
2. The action must retrieve and display the following attributes per object: Object Key, Size (formatted in human-readable units, e.g., "1.2 MB"), and Last Modified timestamp.
3. STDOUT must present the object list as a formatted ASCII table with columns: Object Key, Size, Last Modified, using `tabulate` with `tablefmt="rounded_outline"`.
4. The number of objects returned must be capped at the value defined by the `UE_MAX_OUTPUT_RECORDS` environment variable (default: 100).
5. When the cap is reached and additional objects exist in the bucket, the action must emit a truncation warning in STDOUT indicating that results are limited.
6. The `truncated` flag in the Extension Output JSON must be set to `true` when the result set is capped, and `false` otherwise.
7. The total count of objects returned (up to the cap) must be reported in the `Objects Found` output-only field.
8. On success, the `Status` output-only field must contain a human-readable summary (e.g., "Success: Found 42 objects in bucket 'my-bucket'").

## Action 2 — Upload File

**Functional Requirements:**

1. The action must upload a specified local file from the Universal Agent host to the specified AWS S3 bucket at the specified S3 object key.
2. The local file must exist on the agent host at the path provided; if it does not, the action must fail with a validation error before any AWS call is made.
3. On success, the `Uploaded S3 Key` output-only field must contain the destination S3 object key (e.g., "reports/file.pdf").
4. On success, the `Status` output-only field must contain a human-readable summary (e.g., "Success: File uploaded to s3://my-bucket/reports/file.pdf").

---

# Input Requirements

## Action Selection

- **Action** (choice, required): Determines which operation to execute.
  - Options: `List Objects`, `Upload File`
  - Default presented option: `List Objects`
  - Applicability: All actions
  - Behavior: Selecting `Upload File` reveals the upload-specific input fields (Local File Path, S3 Object Key). Those fields are hidden when `List Objects` is selected.

## Connection Parameters

- **AWS Credentials** (credential, required): UAC credential providing the AWS Access Key ID and AWS Secret Access Key.
  - The `Runtime User` attribute of the credential must contain the AWS Access Key ID.
  - The `Runtime Password` attribute of the credential must contain the AWS Secret Access Key.
  - Hint text must guide operators: "Runtime User: AWS Access Key ID | Runtime Password: AWS Secret Access Key."
  - Applicability: Both actions
  - Default Value: None

- **AWS Region** (text, required): The AWS region where the target S3 bucket is located.
  - Example: `us-east-1`
  - Applicability: Both actions
  - Default Value: None

- **Bucket Name** (text, required): The name of the target S3 bucket.
  - Example: `my-demo-bucket`
  - Applicability: Both actions
  - Default Value: None

## Upload-Specific Parameters

These fields are visible and required only when the Action is `Upload File`.

- **Local File Path** (text, required for Upload File): The absolute path to the local file on the Universal Agent host that will be uploaded to S3.
  - Example: `/data/reports/monthly-2024-01.pdf`
  - Applicability: Upload File action only
  - Default Value: None

- **S3 Object Key** (text, required for Upload File): The destination S3 object key (path within the bucket) where the file will be stored.
  - Example: `reports/monthly-2024-01.pdf`
  - Applicability: Upload File action only
  - Default Value: None

---

# Output Requirements

## On Success

### List Objects

- **Return code:** 0
- **Status description:** `"Success: Found <N> objects in bucket '<bucket>'"` — where `<N>` is the count of objects returned (up to the cap) and `<bucket>` is the bucket name.
- **Output-only fields:**
  - `Status` (Text): Human-readable success summary. Marked `extensionStatus: true`.
  - `Objects Found` (Text): The numeric count of objects returned (e.g., `"42"`).
- **Extension Output JSON:**
  ```json
  {
    "result": {
      "bucket": "my-bucket",
      "object_count": 42,
      "truncated": false,
      "objects": [
        { "key": "reports/monthly-2024-01.pdf", "size_bytes": 1258291, "last_modified": "2024-01-15T10:23:00Z" }
      ]
    }
  }
  ```
  - `truncated` is `true` when the result set was capped by `UE_MAX_OUTPUT_RECORDS`.
- **STDOUT output:** Formatted ASCII table with columns Object Key, Size, Last Modified, followed by a truncation warning line when applicable.
- **Success Criteria:**
  1. AWS S3 API call completes without error.
  2. Object list (up to cap) is written to STDOUT in tabular format.
  3. `Status` and `Objects Found` output-only fields are populated.
  4. Extension Output JSON is emitted with `result` object.
  5. Return code is 0.

### Upload File

- **Return code:** 0
- **Status description:** `"Success: File uploaded to s3://<bucket>/<key>"` — where `<bucket>` is the bucket name and `<key>` is the S3 object key.
- **Output-only fields:**
  - `Status` (Text): Human-readable success summary. Marked `extensionStatus: true`.
  - `Uploaded S3 Key` (Text): The destination S3 object key (e.g., `"reports/file.pdf"`).
- **Extension Output JSON:**
  ```json
  {
    "result": {
      "bucket": "my-bucket",
      "key": "folder/file.txt",
      "s3_uri": "s3://my-bucket/folder/file.txt"
    }
  }
  ```
- **STDOUT output:** Confirmation message indicating the source file path and destination S3 URI.
- **Success Criteria:**
  1. Local file exists and is readable.
  2. AWS S3 upload completes without error.
  3. `Status` and `Uploaded S3 Key` output-only fields are populated.
  4. Extension Output JSON is emitted with `result` object.
  5. Return code is 0.

## On Error

### Failure Scenarios

**Authentication Error**
- Description: The AWS Access Key ID or Secret Access Key provided in the credential is invalid.
- Root causes: Wrong Access Key ID, wrong Secret Access Key, or key has been deactivated.
- Return code: 1
- Status description: `"Authentication Error: Invalid AWS Access Key ID or Secret Access Key"`
- Extension Output JSON:
  ```json
  { "error": { "type": "AuthenticationError", "message": "Invalid AWS Access Key ID or Secret Access Key" } }
  ```

**Authorization Error**
- Description: The credentials are valid but the IAM user or role does not have permission to perform the requested S3 operation on the specified bucket.
- Root causes: Missing IAM policy for `s3:ListObjectsV2` or `s3:PutObject` on the target bucket.
- Return code: 1
- Status description: `"Authorization Error: Access denied — check IAM permissions for bucket '<bucket>'"`
- Extension Output JSON:
  ```json
  { "error": { "type": "AuthorizationError", "message": "Access denied — check IAM permissions for bucket '<bucket>'" } }
  ```

**Configuration Error (Bucket Not Found)**
- Description: The specified bucket does not exist, or exists in a different AWS region than specified.
- Root causes: Incorrect bucket name, incorrect region selection.
- Return code: 1
- Status description: `"Configuration Error: Bucket '<bucket>' does not exist or is in a different region"`
- Extension Output JSON:
  ```json
  { "error": { "type": "ConfigurationError", "message": "Bucket '<bucket>' does not exist or is in a different region" } }
  ```

**Validation Error (Local File Not Found) — Upload File action only**
- Description: The file at the specified Local File Path does not exist on the Universal Agent host.
- Root causes: Incorrect path, file not yet present, wrong agent host.
- Return code: 20
- Status description: `"Validation Error: Local file '<path>' not found on the agent host"`
- Extension Output JSON:
  ```json
  { "error": { "type": "ValidationError", "message": "Local file '<path>' not found on the agent host" } }
  ```

**Unexpected Error**
- Description: Any boto3 or system exception not covered by the categories above.
- Root causes: Network connectivity issues, AWS service disruptions, misconfigured environment.
- Return code: 1
- Status description: `"Unexpected Error: <original boto3 error message>"`
- Extension Output JSON:
  ```json
  { "error": { "type": "UnexpectedError", "message": "<original boto3 error message>" } }
  ```

### Input Validation

- Input fields validation is required. Missing required fields must cause the task to fail before any AWS API call is made.
- When Action is `Upload File`, the Local File Path field must be validated to confirm the file exists on the agent host before any AWS call is made.

---

# Authentication Requirements

The extension must support a single authentication method: AWS IAM credentials (static Access Key ID and Secret Access Key). The credentials must be supplied via a UAC credential object attached to the task. The `Runtime User` attribute holds the Access Key ID; the `Runtime Password` attribute holds the Secret Access Key. No fallback to boto3's implicit credential chain (environment variables, `~/.aws/credentials`, IAM instance profile) is required — the credential field is mandatory.

---

# Environment Variables

- **UE_MAX_OUTPUT_RECORDS**: Controls the maximum number of S3 objects returned and displayed in STDOUT during the List Objects action. Default value is `100`. Operators may override this value per-task to retrieve more or fewer objects without modifying the extension code.

---

# Operational Behavior

**Dynamic Choice Fields:**
Not applicable for this extension.

**Cancel Action:**
Standard UAC task cancellation behavior applies. No special cancel handling is required.

**Re-run Capability:**
Both actions are re-runnable without special handling. Uploading the same file to the same S3 object key will overwrite the existing object — this is standard S3 behavior and no special protection is required for MVP scope.

**Progress Reporting:**
No progress bar or intermediate progress reporting is required for MVP scope. STDOUT will display the result upon action completion.

**Dynamic Commands:**
Not applicable for this extension.

---

# Implementation Notes

## Python Compatibility

Targeting compatibility for Python >= 3.11.

## Target Platform

Linux (x86_64). C extension modules with a confirmed `manylinux_2_17_x86_64` wheel are viable in addition to pure-Python modules. All dependencies for this extension (`boto3`, `tabulate`) are pure-Python and carry no binary compatibility concerns.

## Third-Party Services and Tools

**AWS S3 (Amazon Simple Storage Service)**
- Short Description: Cloud object storage service providing the List Objects and Upload File capabilities.
- Version constraints: No specific version constraint; the extension uses the `list_objects_v2` and `put_object` (or equivalent upload) APIs.
- Integration approach: Via the `boto3` Python SDK. `boto3` and all transitive dependencies (`botocore`, `s3transfer`, `jmespath`) must be bundled with the extension.

**boto3**
- Short Description: Official AWS SDK for Python, providing the S3 client.
- Version: 1.43.96
- Type: Pure Python. All runtime dependencies are also pure-Python.

**tabulate**
- Short Description: Formats tabular data as styled ASCII tables for human-readable STDOUT output.
- Version: 0.10.0
- Type: Pure Python.
- Usage: List Objects STDOUT table output using `tablefmt="rounded_outline"`.

## Error Handling

**High-Level Error Categories:**
1. Authentication errors (invalid credentials)
2. Authorization errors (access denied due to IAM permissions)
3. Configuration errors (bucket not found or wrong region)
4. Validation errors (local file not found — Upload File only)
5. Unexpected errors (all other exceptions)

**Error Handling Strategy:** boto3 `ClientError` exceptions must be caught and their error `Code` mapped to the appropriate user-friendly category and message as specified in the Output Requirements. All other exceptions fall into the Unexpected Error category and surface the original error message.

**Recovery Mechanisms:** None required for MVP scope. All errors result in task failure with an informative status message and Extension Output JSON.

## Resource Cleanup

**Cleanup Scenarios:** The boto3 S3 client must be properly closed or released after each action completes, whether on success or failure.

**Strategy:** Standard Python resource management (context managers or explicit close) must be applied to ensure no open connections or file handles are left after task completion.

---

# Requirements Summary

| # | Requirement |
|---|---|
| R-01 | The extension must implement two actions: List Objects and Upload File for AWS S3. |
| R-02 | All dependencies (boto3, tabulate) must be bundled with the extension; nothing may be installed separately on the UAC agent. |
| R-03 | The AWS credential field must be required; fallback to implicit credential chains is not supported. |
| R-04 | AWS Access Key ID must map to the UAC credential `Runtime User` attribute; AWS Secret Access Key must map to `Runtime Password`. |
| R-05 | List Objects must display Object Key, Size (human-readable), and Last Modified per object in a formatted ASCII table (tabulate, `rounded_outline`). |
| R-06 | List Objects must cap output at `UE_MAX_OUTPUT_RECORDS` (default: 100) and emit a truncation warning when the cap is reached. |
| R-07 | The `truncated` flag in Extension Output JSON must accurately reflect whether the List Objects result was capped. |
| R-08 | Three output-only fields must be populated: `Status` (shared), `Objects Found` (List Objects), `Uploaded S3 Key` (Upload File). |
| R-09 | Extension Output JSON must use a `result` wrapper on success and an `error` wrapper on failure. |
| R-10 | Upload File must validate that the local file exists before making any AWS API call. |
| R-11 | Errors must be categorized (Authentication, Authorization, Configuration, Validation, Unexpected) with user-friendly messages and correct return codes. |
| R-12 | Local file not found (Upload File) must return code 20; all other errors must return code 1. |
| R-13 | Upload-specific fields (Local File Path, S3 Object Key) must only be visible when the Upload File action is selected. |

---

# Document Change History

- 2026-09-17 17:42:24: Initial requirements — Moderate Detail
- 2026-09-17: Comprehensive refinement based on 8 clarification questions and user feedback covering credential mapping, output format, output-only fields, Extension Output JSON structure, large-bucket pagination safety, and error categorization.

---

# References

- Original Requirements Document: `memory/requirements.md`
- Original Requirements Q&A Document: `memory/agents-memory/requirements-QnA.md`
